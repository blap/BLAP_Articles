# core/data_access/tag_repository.py
import duckdb
from .. import database
from ..models import Tag

def add(name: str, tag_id: int) -> int:
    """Adiciona uma nova tag. Se a tag já existir, retorna o ID existente."""
    con = database.get_connection()
    result = con.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
    if result:
        con.close()
        return result[0]

    con.execute("INSERT INTO tags (id, name) VALUES (?, ?)", (tag_id, name))
    con.close()
    return tag_id

def add_to_item(item_id: int, tag_id: int) -> bool:
    """Adiciona uma tag a um item."""
    con = database.get_connection()
    try:
        con.execute("INSERT INTO item_tags (item_id, tag_id) VALUES (?, ?)", (item_id, tag_id))
    except duckdb.ConstraintException:
        pass  # Associação já existe
    finally:
        con.close()
    return True

def get_for_item(item_id: int) -> list[dict]:
    """Retorna todas as tags para um item específico."""
    con = database.get_connection()
    tags = con.execute("""
        SELECT t.id, t.name
        FROM tags t JOIN item_tags it ON t.id = it.tag_id
        WHERE it.item_id = ? ORDER BY t.name
    """, (item_id,)).fetchall()
    con.close()
    return [{'id': row[0], 'name': row[1]} for row in tags]

def tag_exists(tag_id: int) -> bool:
    """Verifica se uma tag com o ID fornecido existe."""
    con = database.get_connection()
    result = con.execute("SELECT 1 FROM tags WHERE id = ?", (tag_id,)).fetchone()
    con.close()
    return result is not None
