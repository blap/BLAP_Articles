from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class Creator:
    id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    creator_type: Optional[str] = None

@dataclass
class Collection:
    id: int
    name: str
    parent_id: Optional[int]

@dataclass
class Tag:
    id: int
    name: str

@dataclass
class Attachment:
    id: int
    item_id: int
    path: str
    mime_type: Optional[str]
    date_added: datetime

@dataclass
class Item:
    id: Optional[int] = None
    item_type: str = 'journalArticle'
    title: Optional[str] = None
    creators: List[Creator] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    tags: List[Tag] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)
    date_added: Optional[datetime] = None
    date_modified: Optional[datetime] = None
