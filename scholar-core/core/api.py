# core/api.py
"""
Este módulo atua como uma fachada (Facade) para a lógica de negócio principal
da aplicação. Ele delega as chamadas para os módulos de serviço apropriados,
mantendo uma API pública estável para a GUI e outros consumidores.
"""

from .models import Item
from .services import item_service, collection_service, tag_service, attachment_service

def add_item(item: Item) -> Item:
    """Adiciona um novo item à biblioteca."""
    return item_service.add_item(item)

def get_item(item_id: int) -> Item | None:
    """Recupera todos os dados de um item."""
    return item_service.get_item(item_id)

def delete_item(item_id: int) -> bool:
    """Exclui um item e todos os seus dados associados."""
    return item_service.delete_item(item_id)

def update_item(item_id: int, update_data: dict) -> bool:
    """Atualiza os dados de um item existente."""
    return item_service.update_item(item_id, update_data)

def add_collection(name: str, parent_id: int | None = None) -> int:
    """Adiciona uma nova coleção."""
    return collection_service.add_collection(name, parent_id)

def add_item_to_collection(item_id: int, collection_id: int) -> bool:
    """Adiciona um item a uma coleção."""
    return collection_service.add_item_to_collection(item_id, collection_id)

def get_items_in_collection(collection_id: int) -> list:
    """Retorna uma lista de resumos de itens em uma coleção."""
    return collection_service.get_items_in_collection(collection_id)

def get_all_collections():
    """Retorna uma lista de todas as coleções."""
    return collection_service.get_all_collections()

def add_tag(name: str) -> int:
    """Adiciona uma nova tag."""
    return tag_service.add_tag(name)

def add_tag_to_item(item_id: int, tag_id: int) -> bool:
    """Adiciona uma tag a um item."""
    return tag_service.add_tag_to_item(item_id, tag_id)

def get_item_tags(item_id: int) -> list:
    """Retorna uma lista de tags para um item específico."""
    return tag_service.get_item_tags(item_id)

def add_attachment(item_id: int, source_path_str: str):
    """Copia um arquivo para a biblioteca e o anexa a um item."""
    return attachment_service.add_attachment(item_id, source_path_str)

def create_item_from_pdf(file_path_str: str) -> Item | None:
    """Cria um novo item a partir de um arquivo PDF."""
    return item_service.create_item_from_pdf(file_path_str)

def search_items(query: str) -> list:
    """Busca itens por um termo no título ou nos metadados."""
    return item_service.search_items(query)

def get_all_items_summary() -> list:
    """Retorna uma lista de resumos de todos os itens."""
    return item_service.get_all_items_summary()
