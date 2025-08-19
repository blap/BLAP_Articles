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

    # 3. Processar e inserir criadores
    creators_data = item_data.get('creators', [])
    if creators_data:
        item_creators_to_insert = []
        for index, creator in enumerate(creators_data):
            first_name = creator.get('first_name')
            last_name = creator.get('last_name')
            creator_type = creator.get('creator_type', 'author')

            # Verificar se o criador já existe
            result = con.execute(
                "SELECT id FROM creators WHERE first_name = ? AND last_name = ?",
                (first_name, last_name)
            ).fetchone()

            if result:
                creator_id = result[0]
            else:
                # Inserir novo criador. Adicionar o índice ao timestamp ajuda a garantir
                # um ID único se vários criadores forem adicionados na mesma fração de segundo.
                creator_id = int(time.time() * 1_000_000) + index
                con.execute(
                    "INSERT INTO creators (id, first_name, last_name) VALUES (?, ?, ?)",
                    (creator_id, first_name, last_name)
                )

            item_creators_to_insert.append((item_id, creator_id, creator_type, index))

        # Inserir as associações item-criador
        con.executemany(
            "INSERT INTO item_creators (item_id, creator_id, creator_type, order_index) VALUES (?, ?, ?, ?)",
            item_creators_to_insert
        )

    con.close()
    print(f"Item {item_id} adicionado com sucesso.")
    return item_id

def get_item(item_id: int) -> dict | None:
    """
    Recupera todos os dados de um item, incluindo metadados e criadores.
    Retorna um dicionário com os dados do item ou None se não for encontrado.
    """
    con = database.get_connection()

    # 1. Obter os dados principais do item
    item_row = con.execute("SELECT id, item_type, title, date_added, date_modified FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item_row:
        con.close()
        return None

    item_result = {
        'id': item_row[0],
        'item_type': item_row[1],
        'title': item_row[2],
        'date_added': item_row[3],
        'date_modified': item_row[4],
        'metadata': {},
        'creators': []
    }

    # 2. Obter metadados
    metadata_rows = con.execute("SELECT field, value FROM metadata WHERE item_id = ?", (item_id,)).fetchall()
    for row in metadata_rows:
        item_result['metadata'][row[0]] = row[1]

    # 3. Obter criadores
    creator_rows = con.execute("""
        SELECT c.first_name, c.last_name, ic.creator_type
        FROM item_creators ic
        JOIN creators c ON ic.creator_id = c.id
        WHERE ic.item_id = ?
        ORDER BY ic.order_index
    """, (item_id,)).fetchall()

    for row in creator_rows:
        item_result['creators'].append({
            'first_name': row[0],
            'last_name': row[1],
            'creator_type': row[2]
        })

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
