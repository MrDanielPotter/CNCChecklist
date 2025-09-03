from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

@dataclass
class ItemAudit:
    timestamp: str
    action: str
    details: Dict

@dataclass
class ChecklistItem:
    id: str
    text: str
    hint: str
    critical: bool = False
    status: Optional[bool] = None  # True=✓, False=✗, None=не начато
    note: str = ""
    photos: List[str] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_sec: Optional[int] = None
    bypassed_by_master: Optional[str] = None  # ФИО мастера при обходе критического
    audit: List[ItemAudit] = field(default_factory=list)

@dataclass
class Block:
    id: str
    title: str
    items: List[ChecklistItem]

@dataclass
class SessionState:
    order_number: str
    started_at: str
    blocks: List[Block]
    current_block_idx: int = 0
    current_item_idx: int = 0
    version: str = "1.3"

@dataclass
class Settings:
    admin_pin_hash: str
    master_pin_hash: str
    pins_must_change: bool = True
    pin_error_count: int = 0
    pin_lock_until_ts: Optional[float] = None
    saf_tree_uri: Optional[str] = None
    smtp_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_tls: bool = True
    smtp_ssl: bool = False
    smtp_user: str = ""
    smtp_pass_app: str = ""
    smtp_recipients: List[str] = field(default_factory=list)
    report_seq: int = 1  # авто-нумерация
