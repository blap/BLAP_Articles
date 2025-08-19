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
