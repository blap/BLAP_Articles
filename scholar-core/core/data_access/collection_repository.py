# core/data_access/collection_repository.py
import duckdb
from .. import database
from ..models import Collection

def add(name: str, parent_id: int | None, collection_id: int) -> int:
    """Adiciona uma nova coleção ao banco de dados."""
    con = database.get_connection()
    con.execute("INSERT INTO collections (id, name, parent_id) VALUES (?, ?, ?)", (collection_id, name, parent_id))
    con.close()
    return collection_id

def add_item_to(item_id: int, collection_id: int) -> bool:
    """Adiciona um item a uma coleção."""
    con = database.get_connection()
    try:
        con.execute("INSERT INTO item_collections (item_id, collection_id) VALUES (?, ?)", (item_id, collection_id))
    except duckdb.ConstraintException:
        pass  # Associação já existe
    finally:
        con.close()
    return True

def get_items_in(collection_id: int) -> list:
    """Retorna uma lista de resumos de itens em uma coleção específica."""
    con = database.get_connection()
    items = con.execute("""
        SELECT
            i.id, i.item_type, i.title,
            (SELECT c.last_name FROM creators c JOIN item_creators ic_sub ON c.id = ic_sub.creator_id
             WHERE ic_sub.item_id = i.id AND ic_sub.creator_type = 'author'
             ORDER BY ic_sub.order_index LIMIT 1) AS first_author
        FROM items i JOIN item_collections ic ON i.id = ic.item_id
        WHERE ic.collection_id = ? ORDER BY i.date_added DESC
    """, (collection_id,)).fetchall()
    con.close()
    return [{'id': row[0], 'item_type': row[1], 'title': row[2], 'author_text': row[3] if row[3] else ''} for row in items]

def get_all() -> list[Collection]:
    """Retorna uma lista de todas as coleções."""
    con = database.get_connection()
    rows = con.execute("SELECT id, name, parent_id FROM collections ORDER BY name").fetchall()
    con.close()
    return [Collection(id=row[0], name=row[1], parent_id=row[2]) for row in rows]

def collection_exists(collection_id: int) -> bool:
    """Verifica se uma coleção com o ID fornecido existe."""
    con = database.get_connection()
    result = con.execute("SELECT 1 FROM collections WHERE id = ?", (collection_id,)).fetchone()
    con.close()
    return result is not None
