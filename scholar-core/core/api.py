# core/api.py
import time
from . import database

def add_item(item_data: dict) -> int:
    """
    Adiciona um novo item à biblioteca.
    `item_data` é um dicionário com 'item_type', 'metadata', 'creators'.
    Retorna o ID do novo item.
    """
    con = database.get_connection()

    # Usar um timestamp de alta precisão como ID
    item_id = int(time.time() * 1_000_000)

    # 1. Inserir na tabela 'items'
    con.execute(
        "INSERT INTO items (id, item_type, title) VALUES (?, ?, ?)",
        (item_id, item_data.get('item_type'), item_data.get('metadata', {}).get('title'))
    )

    # 2. Inserir metadados
    if 'metadata' in item_data:
        metadata_to_insert = [
            (item_id, k, v) for k, v in item_data.get('metadata', {}).items()
        ]
        if metadata_to_insert:
            con.executemany("INSERT INTO metadata (item_id, field, value) VALUES (?, ?, ?)", metadata_to_insert)

    # 3. Processar e inserir criadores (lógica mais complexa aqui)
    # ...

    con.close()
    print(f"Item {item_id} adicionado com sucesso.")
    return item_id

def get_item(item_id: int) -> dict:
    """Recupera todos os dados de um item."""
    # Lógica para consultar o banco e montar o dicionário do item
    pass

def get_all_items_summary() -> list:
    """Retorna uma lista de resumos de todos os itens para exibição na GUI."""
    con = database.get_connection()
    # Query para juntar 'items', 'metadata' (para título) e 'item_creators'
    # Exemplo simplificado:
    items = con.execute("""
        SELECT i.id, i.item_type, i.title
        FROM items i
        ORDER BY i.date_added DESC
    """).fetchall()
    con.close()
    return [{'id': row[0], 'item_type': row[1], 'title': row[2]} for row in items]

# ... outras funções: update_item, delete_item, get_items_by_collection, etc.
