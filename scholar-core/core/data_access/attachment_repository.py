# core/data_access/attachment_repository.py
from .. import database
from ..models import Attachment

def add(item_id: int, attachment_id: int, db_path: str, mime_type: str | None) -> None:
    """Adiciona um novo anexo ao banco de dados."""
    con = database.get_connection()
    con.execute(
        "INSERT INTO attachments (id, item_id, path, mime_type) VALUES (?, ?, ?, ?)",
        (attachment_id, item_id, db_path, mime_type)
    )
    con.close()
