# core/services/tag_service.py
import time
from ..data_access import tag_repository, item_repository
from ..models import Tag

def add_tag(name: str) -> int:
    """Adiciona uma nova tag, gerando um ID se necessário."""
    tag_id = int(time.time() * 1_000_000)
    return tag_repository.add(name, tag_id)

def add_tag_to_item(item_id: int, tag_id: int) -> bool:
    """Adiciona uma tag a um item, verificando se ambos existem."""
    if not item_repository.item_exists(item_id) or not tag_repository.tag_exists(tag_id):
        return False

    return tag_repository.add_to_item(item_id, tag_id)

def get_item_tags(item_id: int) -> list:
    """Retorna as tags de um item."""
    if not item_repository.item_exists(item_id):
        return []
    return tag_repository.get_for_item(item_id)
