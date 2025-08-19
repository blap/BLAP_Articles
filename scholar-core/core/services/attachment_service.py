# core/services/attachment_service.py
import time
import shutil
import mimetypes
import os
from pathlib import Path

from ..models import Attachment
from ..data_access import item_repository, attachment_repository
from .. import database

def add_attachment(item_id: int, source_path_str: str) -> Attachment | None:
    """Copia um arquivo, o anexa a um item e o salva no banco de dados."""
    source_path = Path(source_path_str)
    if not source_path.exists():
        return None

    if not item_repository.item_exists(item_id):
        return None

    storage_dir = os.path.join(database.DATA_DIR, "storage")
    attachment_id = int(time.time() * 1_000_000)
    attachment_dir = os.path.join(storage_dir, str(attachment_id))
    os.makedirs(attachment_dir, exist_ok=True)

    destination_path = os.path.join(attachment_dir, source_path.name)
    shutil.copy(source_path, destination_path)

    mime_type, _ = mimetypes.guess_type(destination_path)
    db_path = os.path.relpath(destination_path, storage_dir)

    attachment_repository.add(item_id, attachment_id, db_path, mime_type)

    new_attachment = Attachment(
        id=attachment_id,
        item_id=item_id,
        path=db_path,
        mime_type=mime_type,
        date_added=None # A data é adicionada pelo DB, não a retornamos aqui
    )
    return new_attachment
