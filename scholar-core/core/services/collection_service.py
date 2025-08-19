# core/services/collection_service.py
import time
from ..data_access import collection_repository, item_repository
from ..models import Collection

def add_collection(name: str, parent_id: int | None = None) -> int:
    """Adiciona uma nova coleção."""
    collection_id = int(time.time() * 1_000_000)
    return collection_repository.add(name, parent_id, collection_id)

def add_item_to_collection(item_id: int, collection_id: int) -> bool:
    """Adiciona um item a uma coleção, verificando se ambos existem."""
    if not item_repository.item_exists(item_id) or not collection_repository.collection_exists(collection_id):
        return False

    return collection_repository.add_item_to(item_id, collection_id)

def get_items_in_collection(collection_id: int) -> list:
    """Retorna os itens de uma coleção."""
    if not collection_repository.collection_exists(collection_id):
        return []
    return collection_repository.get_items_in(collection_id)

def get_all_collections() -> list[Collection]:
    """Retorna todas as coleções."""
    return collection_repository.get_all()
