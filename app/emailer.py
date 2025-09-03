import smtplib, ssl, os, logging
from email.message import EmailMessage

logger = logging.getLogger(__name__)

def send_mail(smtp_conf:dict, subject:str, body:str, attachments:list[str]):
    logger.info(f"Отправка email: {subject}")
    logger.info(f"Получатели: {smtp_conf.get('smtp_recipients', [])}")
    logger.info(f"Вложения: {attachments}")
    
    try:
        msg = EmailMessage()
        msg["From"] = smtp_conf["smtp_user"]
        msg["To"] = ", ".join(smtp_conf.get("smtp_recipients", []))
        msg["Subject"] = subject
        msg.set_content(body)
        logger.info("Email сообщение создано")

        for p in attachments:
            logger.info(f"Добавление вложения: {p}")
            with open(p,"rb") as f:
                data = f.read()
            msg.add_attachment(data, maintype="application", subtype="pdf", filename=os.path.basename(p))
            logger.info(f"Вложение {os.path.basename(p)} добавлено")

        if smtp_conf.get("smtp_ssl"):
            logger.info("Использование SSL соединения")
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_conf["smtp_host"], smtp_conf["smtp_port"], context=ctx) as s:
                logger.info("Подключение к SMTP серверу")
                s.login(smtp_conf["smtp_user"], smtp_conf["smtp_pass_app"])
                logger.info("Авторизация успешна")
                s.send_message(msg)
                logger.info("Email отправлен успешно")
        else:
            logger.info("Использование обычного SMTP соединения")
            with smtplib.SMTP(smtp_conf["smtp_host"], smtp_conf["smtp_port"]) as s:
                if smtp_conf.get("smtp_tls"): 
                    logger.info("Включение TLS")
                    s.starttls()
                logger.info("Подключение к SMTP серверу")
                s.login(smtp_conf["smtp_user"], smtp_conf["smtp_pass_app"])
                logger.info("Авторизация успешна")
                s.send_message(msg)
                logger.info("Email отправлен успешно")
    except Exception as e:
        logger.error(f"Ошибка при отправке email: {e}")
        raise
