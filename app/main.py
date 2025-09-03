import os, time, json, io, logging
from datetime import datetime
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from .models import SessionState, Settings
from .checklist_data import make_blocks
from .persistence import load_json, save_json, sha, now_ts
from .pdf_report import generate_pdf
from . import android_utils
from . import emailer

# Импорт системы логирования и диагностики
from .logging_config import setup_logging, log_app_info, log_performance, audit_logger
from .diagnostics import DiagnosticsCollector
from .performance_monitor import performance_monitor, monitor_performance

APP_VERSION = "1.3"
DEFAULT_MASTER_PIN = "2969"
DEFAULT_ADMIN_PIN = "7717"

AUTO_SAVE_SEC = 10

def j(obj): return json.loads(json.dumps(obj, default=lambda o: o.__dict__))

class RootSM(ScreenManager): pass

class CNCChecklistApp(App):
    def build(self):
        # Настройка логирования
        setup_logging()
        log_app_info()
        
        # Запуск мониторинга производительности
        performance_monitor.start_system_monitoring(interval=60)
        
        logger = logging.getLogger(__name__)
        logger.info("Инициализация приложения CNC Checklist")
        
        try:
            Builder.load_file(os.path.join(os.path.dirname(__file__), "cnc_checklist.kv"))
            logger.info("KV файл загружен успешно")
            
            self.sm = RootSM()
            self.sm.add_widget(Builder.template("StartScreen")())
            self.sm.add_widget(Builder.template("ChecklistScreen")())
            self.sm.add_widget(Builder.template("HistoryScreen")())
            self.sm.add_widget(Builder.template("SettingsScreen")())
            logger.info("Экраны приложения инициализированы")
            
            self.state = None
            self.settings = self._load_settings()
            self.history_index = []
            logger.info("Настройки загружены")
            
            Clock.schedule_interval(lambda dt: self.autosave(), AUTO_SAVE_SEC)
            logger.info(f"Автосохранение настроено каждые {AUTO_SAVE_SEC} секунд")
            
            if platform == "android":
                logger.info("Платформа Android обнаружена, запрашиваем разрешения")
                android_utils.ensure_permissions()
            else:
                logger.info(f"Платформа: {platform}")
                
            logger.info("Приложение успешно инициализировано")
            return self.sm
        except Exception as e:
            logger.error(f"Ошибка при инициализации приложения: {e}")
            raise

    def _load_settings(self)->Settings:
        logger.info("Загрузка настроек приложения")
        d = load_json("settings.json", None)
        if not d:
            logger.info("Настройки не найдены, создаем настройки по умолчанию")
            d = Settings(admin_pin_hash=sha(DEFAULT_ADMIN_PIN),
                         master_pin_hash=sha(DEFAULT_MASTER_PIN)).__dict__
            save_json("settings.json", d)
            logger.info("Настройки по умолчанию сохранены")
        else:
            logger.info("Настройки загружены из файла")
        return Settings(**d)

    # ======== Навигация
    def go_start(self):
        self.sm.current = "start"
    def go_history(self):
        self.refresh_history()
        self.sm.current = "history"
    def open_settings(self):
        self._require_admin_pin(self._open_settings_after_pin)
    def _open_settings_after_pin(self):
        self.sm.current = "settings"
        if self.settings.pins_must_change:
            self._popup_info("Требуется сменить дефолтные PIN-ы в настройках.")

    # ======== Старт сессии
    def start_session(self, order):
        order = (order or "").strip()
        logger.info(f"Попытка начать сессию для заказа: {order}")
        
        if not order or "_" not in order or not order.replace("_","").isdigit():
            logger.warning(f"Неверный формат номера заказа: {order}")
            self._popup_info("Введите номер заказа в формате 123456_78"); return
            
        existing = load_json("session.json", None)
        if existing and not existing.get("completed"):
            logger.info("Найдена незавершенная сессия, предлагаем выбор пользователю")
            # Есть незавершённая — предложить продолжить/сбросить
            box = BoxLayout(orientation='vertical', spacing=8, padding=8)
            box.add_widget(Label(text="Найдена незавершённая сессия."))
            bb = BoxLayout(size_hint_y=None, height='48dp', spacing=8)
            b1 = Button(text="Продолжить")
            b2 = Button(text="Начать заново")
            bb.add_widget(b1); bb.add_widget(b2)
            box.add_widget(bb)
            popup = Popup(title="Выбор", content=box, size_hint=(.8,.4))
            b1.bind(on_release=lambda *_: (popup.dismiss(), self._resume_session(existing)))
            b2.bind(on_release=lambda *_: (popup.dismiss(), self._new_session(order)))
            popup.open()
        else:
            logger.info("Создание новой сессии")
            self._new_session(order)

    def _resume_session(self, d):
        logger.info("Возобновление существующей сессии")
        self.state = SessionState(**d["state"])
        logger.info(f"Сессия возобновлена для заказа: {self.state.order_number}")
        self._enter_checklist()

    @monitor_performance("new_session_creation")
    def _new_session(self, order):
        logger = logging.getLogger(__name__)
        logger.info(f"Создание новой сессии для заказа: {order}")
        audit_logger.log_session_start(order)
        
        blocks = make_blocks()
        self.state = SessionState(order_number=order, started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), blocks=blocks)
        save_json("session.json", {"state": j(self.state), "completed": False})
        logger.info("Новая сессия создана и сохранена")
        self._enter_checklist()

    def _enter_checklist(self):
        self.sm.current = "checklist"
        self._refresh_checklist_ui()

    # ======== Чеклист UI
    def _current(self):
        b = self.state.blocks[self.state.current_block_idx]
        it = b.items[self.state.current_item_idx]
        return b, it

    def _refresh_checklist_ui(self):
        screen = self.sm.get_screen("checklist")
        b, it = self._current()
        screen.ids.header.text = f"{b.title}  [{self.state.current_block_idx+1}/{len(self.state.blocks)}]"
        screen.ids.item_text.text = f"{it.id}. {it.text}"
        # Прогресс
        total = sum(len(x.items) for x in self.state.blocks)
        done = sum(1 for bl in self.state.blocks for i in bl.items if i.completed_at)
        screen.ids.progress.value = 100*done/max(1,total)

    def show_hint(self):
        _, it = self._current()
        self._popup_info(f"Подсказка:\n{it.hint}")

    def add_note(self):
        _, it = self._current()
        ti = TextInput(text=it.note, multiline=True)
        box = BoxLayout(orientation='vertical', spacing=8, padding=8)
        box.add_widget(ti)
        bb = BoxLayout(size_hint_y=None, height='48dp', spacing=8)
        b = Button(text="Сохранить"); bb.add_widget(b); box.add_widget(bb)
        p = Popup(title="Заметка", content=box, size_hint=(.9,.6))
        b.bind(on_release=lambda *_:(setattr(it,'note',ti.text), p.dismiss(), self.autosave()))
        p.open()

    def add_photo(self):
        photos_dir = os.path.join(self.user_data_dir, "photos")
        os.makedirs(photos_dir, exist_ok=True)
        fname = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
        fpath = os.path.join(photos_dir, fname)
        uri = android_utils.take_photo_to(fpath)
        if uri or os.path.exists(fpath):
            _, it = self._current()
            it.photos.append(fpath)
            self._popup_info("Фото добавлено.")
            self.autosave()
        else:
            self._popup_info("Не удалось получить фото.")

    def mark(self, ok:bool):
        b, it = self._current()
        logger.info(f"Отметка пункта {it.id}: {'✓' if ok else '✗'} (критический: {it.critical})")
        
        if it.started_at is None:
            it.started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Пункт {it.id} начат в {it.started_at}")
            
        # Критический «✗» — блокировка с мастер-PIN
        if not ok and it.critical:
            logger.warning(f"Попытка отметить критический пункт {it.id} как невыполненный, требуется мастер-PIN")
            self._require_master_pin(lambda master_name: self._mark_after_master(it, master_name))
            return
        self._complete_item(it, ok)

    def _mark_after_master(self, it, master_name):
        logger = logging.getLogger(__name__)
        logger.info(f"Мастер {master_name} обходит критический пункт {it.id}")
        audit_logger.log_master_bypass(it.id, master_name)
        
        self._complete_item(it, False)
        it.bypassed_by_master = master_name
        self._popup_info(f"Обход критического пункта мастером: {master_name}")

    def _complete_item(self, it, ok):
        logger = logging.getLogger(__name__)
        
        if it.started_at is None:
            it.started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        it.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        it.status = ok
        logger.info(f"Пункт {it.id} завершен в {it.completed_at} со статусом {'✓' if ok else '✗'}")
        
        # Аудит завершения пункта
        audit_logger.log_item_completion(it.id, ok, it.critical)
        
        # duration
        try:
            t0 = datetime.strptime(it.started_at, "%Y-%m-%d %H:%M:%S")
            t1 = datetime.strptime(it.completed_at, "%Y-%m-%d %H:%M:%S")
            it.duration_sec = int((t1 - t0).total_seconds())
            logger.info(f"Пункт {it.id} выполнялся {it.duration_sec} секунд")
        except Exception as e:
            logger.error(f"Ошибка при вычислении времени выполнения пункта {it.id}: {e}")
            it.duration_sec = None
        self.autosave()
        self._refresh_checklist_ui()

    def next_item(self):
        b = self.state.blocks[self.state.current_block_idx]
        it = b.items[self.state.current_item_idx]
        # Нельзя идти дальше, если критический «✗» и не было обхода
        if it.critical and it.status is False and not it.bypassed_by_master:
            self._popup_info("Критический пункт не выполнен — требуется обход мастером."); return
        if self.state.current_item_idx + 1 < len(b.items):
            self.state.current_item_idx += 1
        else:
            # следующий блок
            if self.state.current_block_idx + 1 < len(self.state.blocks):
                self.state.current_block_idx += 1
                self.state.current_item_idx = 0
            else:
                self._popup_info("Все пункты пройдены. Можно завершать.")
        self._refresh_checklist_ui()

    def prev_item(self):
        if self.state.current_item_idx > 0:
            self.state.current_item_idx -= 1
        elif self.state.current_block_idx > 0:
            self.state.current_block_idx -= 1
            self.state.current_item_idx = 0
        self._refresh_checklist_ui()

    # ======== Завершение и PDF
    @monitor_performance("pdf_generation")
    def finish_and_pdf(self):
        if not self.state: return
        completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_seq = self.settings.report_seq
        self.settings.report_seq += 1
        save_json("settings.json", self.settings.__dict__)

        # Формируем структуру отчёта
        report = {
            "order": self.state.order_number,
            "operator": "",  # при желании добавьте ввод ФИО
            "started_at": self.state.started_at,
            "completed_at": completed_at,
            "version": self.state.version,
            "seq": report_seq,
            "blocks": []
        }
        for b in self.state.blocks:
            report["blocks"].append({
                "title": b.title,
                "items": [i.__dict__ for i in b.items]
            })

        # Имя файла
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        fname = f"{ts}_{self.state.order_number}_nesting_{report_seq:04d}.pdf"

        # Пишем PDF в bytes
        tmp_dir = self.user_data_dir
        tmp_pdf = os.path.join(tmp_dir, fname)
        generate_pdf(report, tmp_pdf)
        audit_logger.log_pdf_generation(report['order'], tmp_pdf)
        
        # Если выбран SAF — копируем в выбранную папку
        saved_uri = None
        if self.settings.saf_tree_uri:
            with open(tmp_pdf, "rb") as f: data = f.read()
            uri = android_utils.create_saf_file(self.settings.saf_tree_uri, fname, "application/pdf")
            if uri:
                android_utils.write_bytes_to_saf(uri, data)
                saved_uri = uri
        # История
        hist = load_json("history.json", [])
        hist.append({"order": report["order"], "file": tmp_pdf, "created_at": completed_at, "seq": report_seq})
        save_json("history.json", hist)

        # SMTP
        if self.settings.smtp_enabled and self.settings.smtp_recipients:
            try:
                emailer.send_mail(self.settings.__dict__, f"Отчёт CNC {report['order']}", "См. вложение", [tmp_pdf])
                audit_logger.log_email_send(report['order'], self.settings.smtp_recipients, True)
            except Exception as e:
                audit_logger.log_email_send(report['order'], self.settings.smtp_recipients, False)
                self._popup_info(f"Ошибка e-mail: {e}")

        self._popup_info("PDF создан. Разрешена фрезеровка детали. Осуществить контроль фрезерования.")
        # Завершаем сессию
        save_json("session.json", {"state": j(self.state), "completed": True})
        audit_logger.log_session_end(self.state.order_number, True)

    # ======== История
    def refresh_history(self):
        hist = load_json("history.json", [])
        screen = self.sm.get_screen("history")
        gl = screen.ids.hist_list
        gl.clear_widgets()
        from kivy.uix.button import Button
        for row in reversed(hist):
            btn = Button(text=f"{row['created_at']}  {row['order']}  →  {os.path.basename(row['file'])}",
                         size_hint_y=None, height='46dp')
            def _open(_btn, path=row["file"]): 
                if platform == "android":
                    from jnius import autoclass, cast
                    Intent = autoclass('android.content.Intent')
                    Uri = autoclass('android.net.Uri')
                    File = autoclass('java.io.File')
                    intent = Intent(Intent.ACTION_VIEW)
                    uri = Uri.fromFile(File(path))
                    intent.setDataAndType(uri, "application/pdf")
                    mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
                    mActivity.startActivity(intent)
                else:
                    os.startfile(path) if os.name == 'nt' else os.system(f'xdg-open "{path}"')
            btn.bind(on_release=_open)
            gl.add_widget(btn)

    def apply_history_filter(self, order: str, ymd: str):
        hist = load_json("history.json", [])
        if order: hist = [h for h in hist if order in h["order"]]
        if ymd: hist = [h for h in hist if h["created_at"].startswith(ymd)]
        save_json("history_filtered.json", hist)
        self.refresh_history()

    # ======== Настройки
    def change_pins(self):
        def ask_pin(title, cb):
            ti = TextInput(password=True, multiline=False)
            box = BoxLayout(orientation='vertical', spacing=8, padding=8)
            box.add_widget(Label(text=title)); box.add_widget(ti)
            b = Button(text="OK", size_hint_y=None, height='44dp')
            box.add_widget(b)
            p = Popup(title="PIN", content=box, size_hint=(.7,.4))
            b.bind(on_release=lambda *_:(p.dismiss(), cb(ti.text)))
            p.open()
        ask_pin("Новый мастер-PIN", lambda mp:
            ask_pin("Новый админ-PIN", lambda ap: self._save_pins(mp, ap)))
    def _save_pins(self, master, admin):
        self.settings.master_pin_hash = sha(master.strip())
        self.settings.admin_pin_hash = sha(admin.strip())
        self.settings.pins_must_change = False
        save_json("settings.json", self.settings.__dict__)
        self._popup_info("PIN-коды обновлены.")

    def choose_folder(self):
        uri = android_utils.choose_saf_folder()
        if uri:
            self.settings.saf_tree_uri = uri
            save_json("settings.json", self.settings.__dict__)
            self._popup_info("Папка сохранения выбрана (SAF).")

    def test_pdf(self):
        if not self.state:
            self._popup_info("Нет активной сессии. Начните и отметьте пару пунктов.")
            return
        self.finish_and_pdf()

    def configure_smtp(self):
        # минимальный UI: для краткости — подсказка
        self._popup_info("Откройте app/settings.json и заполните SMTP (host/port/tls/ssl/user/pass, recipients).")

    def export_logs(self):
        """Экспорт логов и диагностической информации"""
        try:
            logger = logging.getLogger(__name__)
            logger.info("Экспорт диагностической информации")
            
            # Создаем диагностический отчет
            collector = DiagnosticsCollector()
            diagnostics_file = collector.export_diagnostics()
            
            # Экспортируем метрики производительности
            metrics_file = os.path.join(self.user_data_dir, f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            performance_monitor.export_metrics(metrics_file)
            
            self._popup_info(f"Диагностика экспортирована:\n{os.path.basename(diagnostics_file)}\n{os.path.basename(metrics_file)}")
            
        except Exception as e:
            logger.error(f"Ошибка при экспорте диагностики: {e}")
            self._popup_info(f"Ошибка при экспорте: {e}")

    # ======== PIN-охранники
    def _locked(self)->bool:
        if not self.settings.pin_lock_until_ts: return False
        return now_ts() < self.settings.pin_lock_until_ts
    def _register_pin_fail(self):
        self.settings.pin_error_count += 1
        if self.settings.pin_error_count >= 5:
            self.settings.pin_lock_until_ts = now_ts() + 5*60
            self._popup_info("Слишком много ошибок PIN. Блокировка на 5 минут.")
        save_json("settings.json", self.settings.__dict__)
    def _reset_pin_fail(self):
        self.settings.pin_error_count = 0
        self.settings.pin_lock_until_ts = None
        save_json("settings.json", self.settings.__dict__)

    def _require_admin_pin(self, ok_cb):
        if self._locked(): 
            self._popup_info("Ввод PIN заблокирован временно."); return
        self._ask_pin("Введите админ-PIN", self.settings.admin_pin_hash, lambda: ok_cb())
    def _require_master_pin(self, ok_cb):
        if self._locked():
            self._popup_info("Ввод PIN заблокирован временно."); return
        # мастер-пин + ввод ФИО
        def after_ok():
            ti = TextInput(hint_text="ФИО мастера", multiline=False)
            box = BoxLayout(orientation='vertical', spacing=8, padding=8)
            box.add_widget(ti)
            b = Button(text="OK", size_hint_y=None, height='44dp')
            box.add_widget(b)
            p = Popup(title="ФИО мастера", content=box, size_hint=(.7,.4))
            b.bind(on_release=lambda *_:(p.dismiss(), ok_cb(ti.text.strip() or "Мастер")))
            p.open()
        self._ask_pin("Мастер-PIN для обхода", self.settings.master_pin_hash, after_ok)

    def _ask_pin(self, title, expected_hash, ok_cb):
        ti = TextInput(password=True, multiline=False)
        box = BoxLayout(orientation='vertical', spacing=8, padding=8)
        box.add_widget(Label(text=title)); box.add_widget(ti)
        b = Button(text="ОК", size_hint_y=None, height='44dp'); box.add_widget(b)
        p = Popup(title="PIN", content=box, size_hint=(.7,.4))
        def chk(*_):
            if sha(ti.text.strip()) == expected_hash:
                self._reset_pin_fail()
                audit_logger.log_pin_attempt("ADMIN" if "админ" in title.lower() else "MASTER", True)
                p.dismiss(); ok_cb()
            else:
                self._register_pin_fail()
                audit_logger.log_pin_attempt("ADMIN" if "админ" in title.lower() else "MASTER", False)
                self._popup_info("Неверный PIN.")
        b.bind(on_release=chk); p.open()

    # ======== Вспомогательные
    def autosave(self):
        if not self.state: 
            logger.debug("Нет активной сессии для автосохранения")
            return
        try:
            save_json("session.json", {"state": j(self.state), "completed": False})
            logger.debug("Автосохранение выполнено успешно")
        except Exception as e:
            logger.error(f"Ошибка при автосохранении: {e}")
            
    def _popup_info(self, text):
        logger.info(f"Показ сообщения пользователю: {text}")
        Popup(title="Сообщение", content=Label(text=text), size_hint=(.85,.4)).open()

if __name__ == "__main__":
    CNCChecklistApp().run()
