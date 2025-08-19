# tests/test_api.py
import pytest
from core import api, database

import os
from pathlib import Path

TEST_DB_FILE = Path("test_library.duckdb")

@pytest.fixture(autouse=True)
def setup_test_database():
    """
    Garante um banco de dados limpo para cada teste usando um arquivo de banco de dados
    temporário que é excluído após o teste.
    """
    original_db_file = database.DB_FILE
    database.DB_FILE = TEST_DB_FILE

    # Garante que não há um banco de dados de um teste anterior
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

    database.initialize_database()

    yield

    # Limpeza: remove o arquivo do banco de dados de teste
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    if os.path.exists(f"{TEST_DB_FILE}.wal"):
        os.remove(f"{TEST_DB_FILE}.wal")

    database.DB_FILE = original_db_file

def test_add_item_success():
    """Testa se um item é adicionado corretamente."""
    item_data = {
        "item_type": "journalArticle",
        "metadata": {
            "title": "A Test-Driven Approach to Science",
            "doi": "10.1234/test.5678"
        },
        "creators": [] # Simplificado
    }

    item_id = api.add_item(item_data)
    assert isinstance(item_id, int)

    # Verifica se o item foi realmente salvo
    retrieved_items = api.get_all_items_summary()
    assert len(retrieved_items) == 1
    assert retrieved_items[0]['title'] == "A Test-Driven Approach to Science"


def test_add_item_with_creators():
    """Testa a adição de um item com criadores e a lógica de desduplicação."""
    # 1. Adicionar um item com dois novos criadores
    item1_data = {
        "item_type": "book",
        "metadata": {"title": "The Art of Programming"},
        "creators": [
            {"first_name": "Jane", "last_name": "Doe", "creator_type": "author"},
            {"first_name": "John", "last_name": "Smith", "creator_type": "editor"}
        ]
    }
    item1_id = api.add_item(item1_data)

    # Verificar o banco de dados diretamente
    con = database.get_connection()
    creators = con.execute("SELECT first_name, last_name FROM creators ORDER BY last_name").fetchall()
    assert len(creators) == 2
    assert creators[0] == ("Jane", "Doe")
    assert creators[1] == ("John", "Smith")

    item_creators = con.execute("SELECT item_id, creator_id, creator_type, order_index FROM item_creators").fetchall()
    assert len(item_creators) == 2

    # 2. Adicionar um segundo item com um criador existente e um novo
    item2_data = {
        "item_type": "journalArticle",
        "metadata": {"title": "Advanced Python"},
        "creators": [
            {"first_name": "Jane", "last_name": "Doe", "creator_type": "author"},
            {"first_name": "Peter", "last_name": "Jones", "creator_type": "author"}
        ]
    }
    item2_id = api.add_item(item2_data)

    # Verificar o banco de dados novamente
    creators = con.execute("SELECT first_name, last_name FROM creators ORDER BY last_name").fetchall()
    assert len(creators) == 3  # Apenas um novo criador (Peter Jones) deve ser adicionado
    assert creators[0] == ("Jane", "Doe")
    assert creators[1] == ("Peter", "Jones")
    assert creators[2] == ("John", "Smith")

    item_creators = con.execute("SELECT item_id FROM item_creators").fetchall()
    assert len(item_creators) == 4 # 2 do primeiro item, 2 do segundo

    # Verificar se a ligação para o segundo item está correta
    jane_doe_id = con.execute("SELECT id FROM creators WHERE first_name='Jane' AND last_name='Doe'").fetchone()[0]
    links_for_item2 = con.execute("SELECT creator_id FROM item_creators WHERE item_id = ?", (item2_id,)).fetchall()
    assert len(links_for_item2) == 2
    assert (jane_doe_id,) in links_for_item2

    con.close()


def test_get_item():
    """Testa a recuperação de um item completo do banco de dados."""
    # 1. Adicionar um item de teste detalhado
    item_data = {
        "item_type": "book",
        "metadata": {
            "title": "A Complete Guide to DuckDB",
            "publisher": "O'Reilly",
            "year": "2023"
        },
        "creators": [
            {"first_name": "Mark", "last_name": "Richards", "creator_type": "author"},
            {"first_name": "Neal", "last_name": "Ford", "creator_type": "author"}
        ]
    }
    item_id = api.add_item(item_data)
    assert item_id is not None

    # 2. Recuperar o item usando get_item
    retrieved_item = api.get_item(item_id)

    # 3. Verificar os dados recuperados
    assert retrieved_item is not None
    assert retrieved_item['id'] == item_id
    assert retrieved_item['item_type'] == item_data['item_type']

    # Normalizar metadados para comparação (add_item adiciona 'title' duas vezes)
    expected_metadata = item_data['metadata']
    expected_metadata['title'] = item_data['metadata']['title']
    assert retrieved_item['metadata'] == expected_metadata

    # Comparar criadores (a ordem é importante)
    assert len(retrieved_item['creators']) == 2
    assert retrieved_item['creators'][0]['first_name'] == "Mark"
    assert retrieved_item['creators'][1]['last_name'] == "Ford"

    # 4. Testar o caso de item não encontrado
    not_found_item = api.get_item(999999999)
    assert not_found_item is None


def test_delete_item():
    """Testa a exclusão de um item e seus dados associados."""
    # 1. Adicionar um item para deletar
    item_data = {
        "item_type": "report",
        "metadata": {"title": "Annual Report"},
        "creators": [{"first_name": "Corporate", "last_name": "Inc", "creator_type": "author"}]
    }
    item_id = api.add_item(item_data)

    # Verificar se foi adicionado
    assert api.get_item(item_id) is not None
    con = database.get_connection()
    metadata_count = con.execute("SELECT COUNT(*) FROM metadata WHERE item_id = ?", (item_id,)).fetchone()[0]
    assert metadata_count > 0
    con.close()

    # 2. Deletar o item
    delete_result = api.delete_item(item_id)
    assert delete_result is True

    # 3. Verificar se o item e os dados associados foram removidos
    assert api.get_item(item_id) is None

    con = database.get_connection()
    metadata_count = con.execute("SELECT COUNT(*) FROM metadata WHERE item_id = ?", (item_id,)).fetchone()[0]
    assert metadata_count == 0
    item_creators_count = con.execute("SELECT COUNT(*) FROM item_creators WHERE item_id = ?", (item_id,)).fetchone()[0]
    assert item_creators_count == 0
    con.close()

    # 4. Tentar deletar um item que não existe
    delete_non_existent_result = api.delete_item(999999999)
    assert delete_non_existent_result is False


def test_update_item():
    """Testa a atualização dos metadados de um item."""
    # 1. Adicionar um item para atualizar
    item_data = {
        "item_type": "book",
        "metadata": {
            "title": "Initial Title",
            "publisher": "Old Publisher"
        }
    }
    item_id = api.add_item(item_data)
    original_item = api.get_item(item_id)
    assert original_item['metadata']['publisher'] == "Old Publisher"

    # 2. Atualizar o item
    update_data = {
        "metadata": {
            "title": "Updated Title",      # Atualizar campo existente
            "year": "2024"                 # Adicionar novo campo
        }
    }
    # Adicionar uma pequena pausa para garantir que o timestamp de modificação mude
    import time
    time.sleep(0.01)
    update_result = api.update_item(item_id, update_data)
    assert update_result is True

    # 3. Verificar as alterações
    updated_item = api.get_item(item_id)
    assert updated_item is not None
    assert updated_item['title'] == "Updated Title"
    assert updated_item['metadata']['title'] == "Updated Title"
    assert updated_item['metadata']['publisher'] == "Old Publisher" # Não foi alterado
    assert updated_item['metadata']['year'] == "2024"
    assert updated_item['date_modified'] > original_item['date_modified']

    # 4. Tentar atualizar um item que não existe
    update_non_existent_result = api.update_item(999999999, update_data)
    assert update_non_existent_result is False


def test_collections():
    """Testa a criação de coleções e a adição de itens a elas."""
    # 1. Adicionar dois itens
    item1_id = api.add_item({"item_type": "book", "metadata": {"title": "Book One"}})
    item2_id = api.add_item({"item_type": "book", "metadata": {"title": "Book Two"}})

    # 2. Criar uma nova coleção
    collection_name = "My Test Collection"
    collection_id = api.add_collection(collection_name)

    con = database.get_connection()
    coll_from_db = con.execute("SELECT name FROM collections WHERE id = ?", (collection_id,)).fetchone()
    assert coll_from_db[0] == collection_name
    con.close()

    # 3. Adicionar o item 1 à coleção
    result = api.add_item_to_collection(item1_id, collection_id)
    assert result is True

    # 4. Obter itens da coleção
    items_in_coll = api.get_items_in_collection(collection_id)
    assert len(items_in_coll) == 1
    assert items_in_coll[0]['id'] == item1_id
    assert items_in_coll[0]['title'] == "Book One"

    # 5. Testar caso de coleção não existente
    items_in_non_existent_coll = api.get_items_in_collection(999999999)
    assert len(items_in_non_existent_coll) == 0


def test_tags():
    """Testa a criação de tags e a sua associação a itens."""
    # 1. Adicionar um item
    item_id = api.add_item({"item_type": "webpage", "metadata": {"title": "Test Page"}})

    # 2. Adicionar uma nova tag e verificar a idempotência
    tag_name = "test-tag"
    tag_id1 = api.add_tag(tag_name)

    con = database.get_connection()
    tag_count = con.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    assert tag_count == 1
    con.close()

    tag_id2 = api.add_tag(tag_name) # Chamar de novo com o mesmo nome
    assert tag_id1 == tag_id2

    con = database.get_connection()
    tag_count = con.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    assert tag_count == 1 # Nenhuma nova tag deve ser criada
    con.close()

    # 3. Adicionar a tag ao item
    result = api.add_tag_to_item(item_id, tag_id1)
    assert result is True

    # 4. Obter as tags do item e verificar
    item_tags = api.get_item_tags(item_id)
    assert len(item_tags) == 1
    assert item_tags[0]['id'] == tag_id1
    assert item_tags[0]['name'] == tag_name


def test_search_items():
    """Testa a funcionalidade de busca de itens."""
    # 1. Adicionar itens de teste
    api.add_item({
        "item_type": "book",
        "metadata": {"title": "The History of Science"}
    })
    api.add_item({
        "item_type": "journalArticle",
        "metadata": {"title": "A study on duckdb", "abstract": "A deep dive into performance."}
    })
    api.add_item({
        "item_type": "webpage",
        "metadata": {"title": "Python for Beginners", "author": "John Science"}
    })

    # 2. Testar buscas
    # Busca por título
    results_science = api.search_items("science")
    assert len(results_science) == 2

    # Busca por metadados
    results_perf = api.search_items("performance")
    assert len(results_perf) == 1
    assert results_perf[0]['title'] == "A study on duckdb"

    # Busca case-insensitive
    results_python_case = api.search_items("PYTHON")
    assert len(results_python_case) == 1
    assert results_python_case[0]['title'] == "Python for Beginners"

    # Busca sem resultados
    results_none = api.search_items("nonexistentterm")
    assert len(results_none) == 0
