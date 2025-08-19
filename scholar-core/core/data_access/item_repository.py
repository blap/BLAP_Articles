# core/data_access/item_repository.py
from .. import database
from ..models import Item, Creator, Tag, Attachment

def get(item_id: int) -> dict | None:
    """Recupera todos os dados brutos de um item do banco de dados."""
    con = database.get_connection()

    item_row = con.execute("SELECT id, item_type, title, date_added, date_modified FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item_row:
        con.close()
        return None

    item_data = {
        'id': item_row[0],
        'item_type': item_row[1],
        'title': item_row[2],
        'date_added': item_row[3],
        'date_modified': item_row[4],
        'metadata': {},
        'creators': [],
        'tags': [],
        'attachments': []
    }

    metadata_rows = con.execute("SELECT field, value FROM metadata WHERE item_id = ?", (item_id,)).fetchall()
    item_data['metadata'] = {row[0]: row[1] for row in metadata_rows}

    creator_rows = con.execute("""
        SELECT c.id, c.first_name, c.last_name, ic.creator_type
        FROM item_creators ic JOIN creators c ON ic.creator_id = c.id
        WHERE ic.item_id = ? ORDER BY ic.order_index
    """, (item_id,)).fetchall()
    item_data['creators'] = [Creator(id=row[0], first_name=row[1], last_name=row[2], creator_type=row[3]) for row in creator_rows]

    tag_rows = con.execute("""
        SELECT t.id, t.name FROM tags t JOIN item_tags it ON t.id = it.tag_id
        WHERE it.item_id = ? ORDER BY t.name
    """, (item_id,)).fetchall()
    item_data['tags'] = [Tag(id=row[0], name=row[1]) for row in tag_rows]

    attachment_rows = con.execute("""
        SELECT id, item_id, path, mime_type, date_added FROM attachments
        WHERE item_id = ? ORDER BY date_added
    """, (item_id,)).fetchall()
    item_data['attachments'] = [Attachment(id=row[0], item_id=row[1], path=row[2], mime_type=row[3], date_added=row[4]) for row in attachment_rows]

    con.close()
    return item_data

def search(query: str) -> list[dict]:
    """Busca itens por um termo no título ou nos metadados."""
    con = database.get_connection()
    search_term = f"%{query.lower()}%"

    items = con.execute("""
        SELECT DISTINCT i.id, i.item_type, i.title
        FROM items i
        LEFT JOIN metadata m ON i.id = m.item_id
        WHERE lower(i.title) LIKE ? OR lower(m.value) LIKE ?
        ORDER BY i.date_modified DESC
    """, (search_term, search_term)).fetchall()
    con.close()
    return [{'id': row[0], 'item_type': row[1], 'title': row[2]} for row in items]

def get_all_summary() -> list[dict]:
    """Retorna um resumo de todos os itens."""
    con = database.get_connection()
    items = con.execute("""
        SELECT
            i.id, i.item_type, i.title,
            (SELECT c.last_name FROM creators c JOIN item_creators ic ON c.id = ic.creator_id
             WHERE ic.item_id = i.id AND ic.creator_type = 'author'
             ORDER BY ic.order_index LIMIT 1) AS first_author
        FROM items i ORDER BY i.date_added DESC
    """).fetchall()
    con.close()
    return [{'id': row[0], 'item_type': row[1], 'title': row[2], 'author_text': row[3] if row[3] else ''} for row in items]

def add(item: Item) -> None:
    """Adiciona um novo item e seus dados associados ao banco de dados."""
    con = database.get_connection()
    con.execute("INSERT INTO items (id, item_type, title) VALUES (?, ?, ?)", (item.id, item.item_type, item.title))

    if item.metadata:
        metadata_to_insert = [(item.id, k, v) for k, v in item.metadata.items()]
        con.executemany("INSERT INTO metadata (item_id, field, value) VALUES (?, ?, ?)", metadata_to_insert)

    if item.creators:
        item_creators_to_insert = []
        for index, creator in enumerate(item.creators):
            result = con.execute("SELECT id FROM creators WHERE first_name = ? AND last_name = ?", (creator.first_name, creator.last_name)).fetchone()
            if result:
                creator.id = result[0]
            else:
                con.execute("INSERT INTO creators (id, first_name, last_name) VALUES (?, ?, ?)", (creator.id, creator.first_name, creator.last_name))
            item_creators_to_insert.append((item.id, creator.id, creator.creator_type, index))
        con.executemany("INSERT INTO item_creators (item_id, creator_id, creator_type, order_index) VALUES (?, ?, ?, ?)", item_creators_to_insert)
    con.close()

def update(item_id: int, update_data: dict) -> None:
    """Atualiza os dados de um item existente."""
    con = database.get_connection()
    if 'metadata' in update_data:
        metadata_to_upsert = [(item_id, k, v) for k, v in update_data['metadata'].items()]
        if metadata_to_upsert:
            con.executemany("INSERT INTO metadata (item_id, field, value) VALUES (?, ?, ?) ON CONFLICT (item_id, field) DO UPDATE SET value = excluded.value", metadata_to_upsert)
            if 'title' in update_data['metadata']:
                con.execute("UPDATE items SET title = ? WHERE id = ?", (update_data['metadata']['title'], item_id))
    con.execute("UPDATE items SET date_modified = current_timestamp WHERE id = ?", (item_id,))
    con.close()

def delete(item_id: int) -> bool:
    """Exclui um item e seus dados associados."""
    con = database.get_connection()
    item_exists = con.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item_exists:
        con.close()
        return False

    con.execute("DELETE FROM item_creators WHERE item_id = ?", (item_id,))
    con.execute("DELETE FROM metadata WHERE item_id = ?", (item_id,))
    con.execute("DELETE FROM item_tags WHERE item_id = ?", (item_id,))
    con.execute("DELETE FROM item_collections WHERE item_id = ?", (item_id,))
    con.execute("DELETE FROM attachments WHERE item_id = ?", (item_id,))
    con.execute("DELETE FROM items WHERE id = ?", (item_id,))
    con.close()
    return True

def item_exists(item_id: int) -> bool:
    """Verifica se um item com o ID fornecido existe."""
    con = database.get_connection()
    result = con.execute("SELECT 1 FROM items WHERE id = ?", (item_id,)).fetchone()
    con.close()
    return result is not None
