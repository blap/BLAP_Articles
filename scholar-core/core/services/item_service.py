# core/services/item_service.py
import time
import re
import requests
from pathlib import Path
from PyPDF2 import PdfReader

from ..models import Item, Creator
from ..data_access import item_repository, attachment_repository
from ..plugin_manager import manager as plugin_manager
from . import attachment_service

def add_item(item: Item) -> Item:
    """
    Adiciona um novo item à biblioteca, orquestrando a lógica de negócio.
    """
    # Gerar IDs
    item.id = int(time.time() * 1_000_000)
    if item.creators:
        for index, creator in enumerate(item.creators):
            creator.id = int(time.time() * 1_000_000) + index

    # Garantir que o título do item esteja sincronizado com os metadados
    if item.metadata:
        item.metadata['title'] = item.title

    item_repository.add(item)

    plugin_manager.hook_item_added(item.id)
    return item

def get_item(item_id: int) -> Item | None:
    """Recupera um item completo, convertendo dados brutos em um objeto de modelo."""
    item_data = item_repository.get(item_id)
    if not item_data:
        return None

    return Item(**item_data)

def delete_item(item_id: int) -> bool:
    """Deleta um item e chama o hook do plugin."""
    deleted = item_repository.delete(item_id)
    if deleted:
        plugin_manager.hook_item_deleted(item_id)
    return deleted

def update_item(item_id: int, update_data: dict) -> bool:
    """Atualiza um item e chama o hook do plugin."""
    if not item_repository.item_exists(item_id):
        return False

    item_repository.update(item_id, update_data)
    plugin_manager.hook_item_updated(item_id)
    return True

def search_items(query: str) -> list[dict]:
    """Busca itens."""
    return item_repository.search(query)

def get_all_items_summary() -> list[dict]:
    """Retorna um resumo de todos os itens."""
    return item_repository.get_all_summary()

def create_item_from_pdf(file_path_str: str) -> Item | None:
    """
    Cria um item a partir de um PDF, extraindo metadados e anexando o arquivo.
    """
    file_path = Path(file_path_str)
    if not file_path.exists():
        return None

    try:
        reader = PdfReader(file_path)
        pdf_meta = reader.metadata
        title = pdf_meta.title or file_path.stem.replace('_', ' ').replace('-', ' ')

        doi = None
        for page in reader.pages:
            text = page.extract_text()
            match = re.search(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', text, re.IGNORECASE)
            if match:
                doi = match.group(0)
                break

        item = Item(title=title, item_type='journalArticle')
        item.metadata['source_file'] = file_path.name

        if doi:
            item.metadata['doi'] = doi
            try:
                resp = requests.get(f"https://api.crossref.org/works/{doi}")
                if resp.ok:
                    crossref_data = resp.json()['message']
                    item.title = crossref_data.get('title', [item.title])[0]
                    item.metadata['title'] = item.title
                    if 'author' in crossref_data:
                        item.creators = [Creator(first_name=author.get('given'), last_name=author.get('family'), creator_type='author') for author in crossref_data['author']]
            except requests.RequestException:
                pass

        new_item = add_item(item)
        attachment_service.add_attachment(new_item.id, file_path_str)
        return get_item(new_item.id)

    except Exception as e:
        print(f"Erro ao processar PDF {file_path_str}: {e}")
        return None
