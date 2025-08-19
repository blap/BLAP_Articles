# core/api.py
import time
from . import database
from .plugin_manager import manager as plugin_manager
import shutil
import mimetypes
import os
from pathlib import Path
from .models import Item, Creator, Tag, Attachment

def add_item(item: Item) -> Item:
    """
    Adiciona um novo item à biblioteca.
    Recebe um objeto Item e retorna o objeto Item com o ID e datas preenchidos.
    """
    con = database.get_connection()

    # Gerar um novo ID para o item
    item.id = int(time.time() * 1_000_000)

    # 1. Inserir na tabela 'items'
    # O título também é armazenado nos metadados, mas tê-lo na tabela principal é bom para buscas rápidas.
    con.execute(
        "INSERT INTO items (id, item_type, title) VALUES (?, ?, ?)",
        (item.id, item.item_type, item.title)
    )

    # 2. Inserir metadados
    if item.metadata:
        # Garante que o título do item esteja sincronizado com os metadados
        item.metadata['title'] = item.title
        metadata_to_insert = [
            (item.id, k, v) for k, v in item.metadata.items()
        ]
        con.executemany("INSERT INTO metadata (item_id, field, value) VALUES (?, ?, ?)", metadata_to_insert)

    # 3. Processar e inserir criadores
    if item.creators:
        item_creators_to_insert = []
        for index, creator in enumerate(item.creators):
            # Verificar se o criador já existe
            result = con.execute(
                "SELECT id FROM creators WHERE first_name = ? AND last_name = ?",
                (creator.first_name, creator.last_name)
            ).fetchone()

            if result:
                creator.id = result[0]
            else:
                # Inserir novo criador
                creator.id = int(time.time() * 1_000_000) + index
                con.execute(
                    "INSERT INTO creators (id, first_name, last_name) VALUES (?, ?, ?)",
                    (creator.id, creator.first_name, creator.last_name)
                )

            item_creators_to_insert.append((item.id, creator.id, creator.creator_type, index))

        # Inserir as associações item-criador
        con.executemany(
            "INSERT INTO item_creators (item_id, creator_id, creator_type, order_index) VALUES (?, ?, ?, ?)",
            item_creators_to_insert
        )

    con.close()

    # Chamar hook de plugin
    plugin_manager.hook_item_added(item.id)

    # Retornar o item completo (sem datas, pois get_item as buscará)
    # Para ter as datas, precisaríamos de outra chamada ao banco.
    # Por enquanto, vamos retornar o item com o ID.
    return item

def get_item(item_id: int) -> Item | None:
    """
    Recupera todos os dados de um item e os retorna como um objeto Item.
    """
    con = database.get_connection()

    item_row = con.execute("SELECT id, item_type, title, date_added, date_modified FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item_row:
        con.close()
        return None

    item_result = Item(
        id=item_row[0],
        item_type=item_row[1],
        title=item_row[2],
        date_added=item_row[3],
        date_modified=item_row[4]
    )

    metadata_rows = con.execute("SELECT field, value FROM metadata WHERE item_id = ?", (item_id,)).fetchall()
    item_result.metadata = {row[0]: row[1] for row in metadata_rows}

    creator_rows = con.execute("""
        SELECT c.id, c.first_name, c.last_name, ic.creator_type
        FROM item_creators ic
        JOIN creators c ON ic.creator_id = c.id
        WHERE ic.item_id = ?
        ORDER BY ic.order_index
    """, (item_id,)).fetchall()

    item_result.creators = [Creator(id=row[0], first_name=row[1], last_name=row[2], creator_type=row[3]) for row in creator_rows]

    tag_rows = con.execute("""
        SELECT t.id, t.name
        FROM tags t
        JOIN item_tags it ON t.id = it.tag_id
        WHERE it.item_id = ?
        ORDER BY t.name
    """, (item_id,)).fetchall()
    item_result.tags = [Tag(id=row[0], name=row[1]) for row in tag_rows]

    attachment_rows = con.execute("""
        SELECT id, item_id, path, mime_type, date_added
        FROM attachments
        WHERE item_id = ?
        ORDER BY date_added
    """, (item_id,)).fetchall()
    item_result.attachments = [Attachment(id=row[0], item_id=row[1], path=row[2], mime_type=row[3], date_added=row[4]) for row in attachment_rows]

    con.close()
    return item_result


def delete_item(item_id: int) -> bool:
    """
    Exclui um item e todos os seus dados associados do banco de dados.
    Retorna True se o item foi excluído, False caso contrário.
    """
    con = database.get_connection()

    # Verificar se o item existe
    item_exists = con.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item_exists:
        con.close()
        return False

    # Exclusão em cascata manual
    con.execute("DELETE FROM item_creators WHERE item_id = ?", (item_id,))
    con.execute("DELETE FROM metadata WHERE item_id = ?", (item_id,))
    con.execute("DELETE FROM item_tags WHERE item_id = ?", (item_id,))
    con.execute("DELETE FROM item_collections WHERE item_id = ?", (item_id,))
    con.execute("DELETE FROM attachments WHERE item_id = ?", (item_id,))

    # Finalmente, excluir o item principal
    con.execute("DELETE FROM items WHERE id = ?", (item_id,))

    con.close()

    # Chamar hook de plugin
    plugin_manager.hook_item_deleted(item_id)

    return True


def update_item(item_id: int, update_data: dict) -> bool:
    """
    Atualiza os dados de um item existente. No momento, focado em metadados.
    Retorna True se o item foi atualizado, False caso contrário.
    """
    con = database.get_connection()

    # Verificar se o item existe
    item_exists = con.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item_exists:
        con.close()
        return False

    # 1. Atualizar metadados
    if 'metadata' in update_data:
        metadata_to_upsert = [
            (item_id, k, v) for k, v in update_data['metadata'].items()
        ]
        if metadata_to_upsert:
            con.executemany(
                """
                INSERT INTO metadata (item_id, field, value) VALUES (?, ?, ?)
                ON CONFLICT (item_id, field) DO UPDATE SET value = excluded.value
                """,
                metadata_to_upsert
            )
            # Se o título for atualizado nos metadados, atualize também na tabela de itens
            if 'title' in update_data['metadata']:
                con.execute("UPDATE items SET title = ? WHERE id = ?", (update_data['metadata']['title'], item_id))

    # 2. Atualizar o timestamp de modificação
    con.execute("UPDATE items SET date_modified = current_timestamp WHERE id = ?", (item_id,))

    con.close()

    # Chamar hook de plugin
    plugin_manager.hook_item_updated(item_id)

    return True


def add_collection(name: str, parent_id: int | None = None) -> int:
    """Adiciona uma nova coleção ao banco de dados."""
    con = database.get_connection()
    collection_id = int(time.time() * 1_000_000)
    con.execute(
        "INSERT INTO collections (id, name, parent_id) VALUES (?, ?, ?)",
        (collection_id, name, parent_id)
    )
    con.close()
    return collection_id


def add_item_to_collection(item_id: int, collection_id: int) -> bool:
    """Adiciona um item a uma coleção, verificando se ambos existem."""
    con = database.get_connection()

    # Verificar se o item e a coleção existem
    item_exists = con.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
    collection_exists = con.execute("SELECT id FROM collections WHERE id = ?", (collection_id,)).fetchone()

    if not item_exists or not collection_exists:
        con.close()
        return False

    # Inserir a associação
    try:
        con.execute(
            "INSERT INTO item_collections (item_id, collection_id) VALUES (?, ?)",
            (item_id, collection_id)
        )
    except con.IntegrityError:
        # A associação já pode existir, o que não é um erro.
        pass
    finally:
        con.close()

    return True


def get_items_in_collection(collection_id: int) -> list:
    """Retorna uma lista de resumos de itens em uma coleção específica."""
    con = database.get_connection()
    items = con.execute("""
        SELECT i.id, i.item_type, i.title
        FROM items i
        JOIN item_collections ic ON i.id = ic.item_id
        WHERE ic.collection_id = ?
        ORDER BY i.date_added DESC
    """, (collection_id,)).fetchall()
    con.close()
    return [{'id': row[0], 'item_type': row[1], 'title': row[2]} for row in items]


def add_tag(name: str) -> int:
    """
    Adiciona uma nova tag. Se a tag já existir, retorna o ID existente.
    """
    con = database.get_connection()

    # Verificar se a tag já existe
    result = con.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
    if result:
        con.close()
        return result[0]

    # Inserir nova tag
    tag_id = int(time.time() * 1_000_000)
    con.execute("INSERT INTO tags (id, name) VALUES (?, ?)", (tag_id, name))
    con.close()
    return tag_id


def add_tag_to_item(item_id: int, tag_id: int) -> bool:
    """Adiciona uma tag a um item, verificando se ambos existem."""
    con = database.get_connection()

    # Verificar se o item e a tag existem
    item_exists = con.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
    tag_exists = con.execute("SELECT id FROM tags WHERE id = ?", (tag_id,)).fetchone()

    if not item_exists or not tag_exists:
        con.close()
        return False

    # Inserir a associação
    try:
        con.execute(
            "INSERT INTO item_tags (item_id, tag_id) VALUES (?, ?)",
            (item_id, tag_id)
        )
    except con.IntegrityError:
        # A associação já pode existir, o que não é um erro.
        pass
    finally:
        con.close()

    return True


def get_item_tags(item_id: int) -> list:
    """Retorna uma lista de tags para um item específico."""
    con = database.get_connection()
    tags = con.execute("""
        SELECT t.id, t.name
        FROM tags t
        JOIN item_tags it ON t.id = it.tag_id
        WHERE it.item_id = ?
        ORDER BY t.name
    """, (item_id,)).fetchall()
    con.close()
    return [{'id': row[0], 'name': row[1]} for row in tags]


def add_attachment(item_id: int, source_path_str: str) -> Attachment | None:
    """Copia um arquivo para a biblioteca e o anexa a um item."""
    source_path = Path(source_path_str)
    if not source_path.exists():
        return None # O arquivo de origem não existe

    con = database.get_connection()

    # Verificar se o item existe
    item_exists = con.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item_exists:
        con.close()
        return None

    # Definir o diretório de armazenamento da biblioteca
    storage_dir = database.DB_FILE.parent / "storage"

    # Gerar um ID para o anexo e criar um subdiretório para ele
    attachment_id = int(time.time() * 1_000_000)
    attachment_dir = storage_dir / str(attachment_id)
    attachment_dir.mkdir(parents=True, exist_ok=True)

    # Copiar o arquivo
    destination_path = attachment_dir / source_path.name
    shutil.copy(source_path, destination_path)

    # Determinar o tipo MIME
    mime_type, _ = mimetypes.guess_type(destination_path)

    # Salvar no banco de dados
    db_path = str(destination_path.relative_to(storage_dir))
    con.execute(
        "INSERT INTO attachments (id, item_id, path, mime_type) VALUES (?, ?, ?, ?)",
        (attachment_id, item_id, db_path, mime_type)
    )
    con.close()

    # Retornar o objeto Attachment
    new_attachment = Attachment(
        id=attachment_id,
        item_id=item_id,
        path=db_path,
        mime_type=mime_type,
        date_added=None # Poderia ser lido do DB para ser preciso
    )
    return new_attachment


def search_items(query: str) -> list:
    """
    Busca itens por um termo no título ou nos metadados.
    A busca não diferencia maiúsculas de minúsculas.
    """
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


def get_all_items_summary() -> list:
    """
    Retorna uma lista de resumos de todos os itens, incluindo um autor principal
    para exibição na GUI.
    """
    con = database.get_connection()
    items = con.execute("""
        SELECT
            i.id,
            i.item_type,
            i.title,
            (SELECT c.last_name
             FROM creators c
             JOIN item_creators ic ON c.id = ic.creator_id
             WHERE ic.item_id = i.id AND ic.creator_type = 'author'
             ORDER BY ic.order_index
             LIMIT 1) AS first_author
        FROM items i
        ORDER BY i.date_added DESC
    """).fetchall()
    con.close()
    return [{
        'id': row[0],
        'item_type': row[1],
        'title': row[2],
        'author_text': row[3] if row[3] else ''
    } for row in items]

# ... outras funções: update_item, delete_item, get_items_by_collection, etc.
