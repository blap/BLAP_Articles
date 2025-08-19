import pytest
from core import api, database
from core.models import Item, Creator, Collection
import os
from pathlib import Path
from unittest.mock import patch, Mock

TEST_DB_FILE = Path("test_library.duckdb")

@pytest.fixture(autouse=True)
def setup_test_database():
    original_db_file = database.DB_FILE
    database.DB_FILE = TEST_DB_FILE
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    database.initialize_database()
    yield
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    if os.path.exists(f"{TEST_DB_FILE}.wal"):
        os.remove(f"{TEST_DB_FILE}.wal")
    database.DB_FILE = original_db_file

def test_add_item_success():
    """Testa se um item é adicionado e recuperado corretamente."""
    item_to_add = Item(
        item_type="journalArticle",
        title="A Test-Driven Approach to Science",
        metadata={"doi": "10.1234/test.5678"},
        creators=[Creator(first_name="Ada", last_name="Lovelace", creator_type="author")]
    )

    added_item = api.add_item(item_to_add)
    assert added_item.id is not None

    retrieved_item = api.get_item(added_item.id)
    assert retrieved_item is not None
    assert retrieved_item.title == "A Test-Driven Approach to Science"
    assert retrieved_item.creators[0].last_name == "Lovelace"

def test_add_item_with_creators_deduplication():
    """Testa a lógica de desduplicação de criadores."""
    creator_jane = Creator(first_name="Jane", last_name="Doe", creator_type="author")
    creator_john = Creator(first_name="John", last_name="Smith", creator_type="editor")

    item1 = Item(item_type="book", title="The Art of Programming", creators=[creator_jane, creator_john])
    api.add_item(item1)

    con = database.get_connection()
    creator_count = con.execute("SELECT COUNT(*) FROM creators").fetchone()[0]
    assert creator_count == 2
    con.close()

    creator_jane_dup = Creator(first_name="Jane", last_name="Doe", creator_type="author")
    creator_peter = Creator(first_name="Peter", last_name="Jones", creator_type="author")
    item2 = Item(item_type="journalArticle", title="Advanced Python", creators=[creator_jane_dup, creator_peter])
    api.add_item(item2)

    con = database.get_connection()
    creator_count = con.execute("SELECT COUNT(*) FROM creators").fetchone()[0]
    assert creator_count == 3  # Apenas um novo criador deve ser adicionado

def test_get_item():
    """Testa a recuperação de um item completo."""
    item_to_add = Item(
        item_type="book",
        title="A Complete Guide to DuckDB",
        metadata={"publisher": "O'Reilly", "year": "2023"},
        creators=[Creator(first_name="Mark", last_name="Richards", creator_type="author")]
    )
    added_item = api.add_item(item_to_add)
    retrieved_item = api.get_item(added_item.id)

    assert retrieved_item is not None
    assert retrieved_item.id == added_item.id
    assert retrieved_item.metadata["publisher"] == "O'Reilly"
    assert len(retrieved_item.creators) == 1
    assert retrieved_item.creators[0].first_name == "Mark"

    assert api.get_item(999999) is None

def test_delete_item():
    """Testa a exclusão de um item."""
    item_to_add = Item(item_type="report", title="Annual Report")
    added_item = api.add_item(item_to_add)

    assert api.get_item(added_item.id) is not None

    delete_result = api.delete_item(added_item.id)
    assert delete_result is True
    assert api.get_item(added_item.id) is None

    assert api.delete_item(999999) is False

def test_update_item():
    """Testa a atualização de um item."""
    item_to_add = Item(item_type="book", title="Initial Title", metadata={"publisher": "Old Publisher"})
    added_item = api.add_item(item_to_add)

    update_data = {"metadata": {"title": "Updated Title", "year": "2024"}}
    api.update_item(added_item.id, update_data)

    updated_item = api.get_item(added_item.id)
    assert updated_item.title == "Updated Title"
    assert updated_item.metadata["year"] == "2024"
    assert updated_item.metadata["publisher"] == "Old Publisher"

def test_collections():
    """Testa a funcionalidade de coleções."""
    item1 = api.add_item(Item(title="Book One"))
    api.add_item(Item(title="Book Two"))
    collection_id = api.add_collection("My Test Collection")

    api.add_item_to_collection(item1.id, collection_id)

    items_in_coll = api.get_items_in_collection(collection_id)
    assert len(items_in_coll) == 1
    assert items_in_coll[0]['id'] == item1.id

def test_tags():
    """Testa a funcionalidade de tags."""
    item = api.add_item(Item(title="Test Page"))
    tag_id = api.add_tag("test-tag")

    api.add_tag_to_item(item.id, tag_id)

    item_tags = api.get_item_tags(item.id)
    assert len(item_tags) == 1
    assert item_tags[0]['name'] == "test-tag"

def test_search_items():
    """Testa a busca de itens."""
    api.add_item(Item(title="The History of Science"))
    api.add_item(Item(title="A study on duckdb", metadata={"abstract": "performance"}))

    results = api.search_items("science")
    assert len(results) == 1

    results_perf = api.search_items("performance")
    assert len(results_perf) == 1

def test_add_item_edge_cases():
    """Testa adicionar itens com dados mínimos."""
    item = api.add_item(Item(item_type="note"))
    retrieved = api.get_item(item.id)
    assert retrieved.title is None
    assert retrieved.metadata == {}

def test_linking_failures():
    """Testa falhas de vinculação."""
    item = api.add_item(Item(title="My Note"))
    collection_id = api.add_collection("My Collection")
    tag_id = api.add_tag("my-tag")

    assert not api.add_item_to_collection(item.id, 999)
    assert not api.add_item_to_collection(999, collection_id)
    assert not api.add_tag_to_item(item.id, 999)
    assert not api.add_tag_to_item(999, tag_id)


@patch('core.api.requests.get')
@patch('core.api.PdfReader')
def test_create_item_from_pdf(MockPdfReader, mock_requests_get):
    """Testa a criação de um item a partir de um arquivo PDF."""
    import tempfile
    import shutil

    # 1. Configurar Mocks
    # Mock para a resposta da API CrossRef
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        'message': {
            'title': ['Mocked PDF Title'],
            'author': [{'given': 'John', 'family': 'Doe'}]
        }
    }
    mock_requests_get.return_value = mock_response

    # Mock para o leitor de PDF
    mock_pdf_instance = MockPdfReader.return_value
    mock_pdf_instance.metadata.title = "Original PDF Title"
    mock_page = Mock()
    mock_page.extract_text.return_value = "Some text with a DOI: 10.1234/mock.doi"
    mock_pdf_instance.pages = [mock_page]

    # 2. Setup: criar um arquivo dummy
    with tempfile.TemporaryDirectory() as temp_dir:
        dummy_file_path = Path(temp_dir) / "test.pdf"
        dummy_file_path.touch() # Criar arquivo vazio, o conteúdo será mockado

        # 3. Chamar a função a ser testada
        item = api.create_item_from_pdf(str(dummy_file_path))

        # 4. Asserts
        assert item is not None
        assert item.title == "Mocked PDF Title"
        assert len(item.creators) == 1
        assert item.creators[0].first_name == "John"
        assert item.metadata['doi'] == "10.1234/mock.doi"

        # Verificar se o anexo foi criado
        assert len(item.attachments) == 1
        assert item.attachments[0].path.endswith("test.pdf")

        # Verificar se a chamada à API foi feita
        mock_requests_get.assert_called_with("https://api.crossref.org/works/10.1234/mock.doi")

        # 5. Limpeza
        shutil.rmtree(database.DB_FILE.parent / "storage")


def test_get_all_collections():
    """Testa a recuperação de todas as coleções."""
    parent_id = api.add_collection("Parent")
    api.add_collection("Child", parent_id=parent_id)

    collections = api.get_all_collections()
    assert len(collections) == 2

    parent_coll = next(c for c in collections if c.name == "Parent")
    child_coll = next(c for c in collections if c.name == "Child")

    assert parent_coll is not None
    assert child_coll is not None
    assert child_coll.parent_id == parent_coll.id


def test_attachments():
    """Testa a adição e recuperação de anexos."""
    import tempfile
    import shutil

    # 1. Setup: criar um arquivo dummy
    with tempfile.TemporaryDirectory() as temp_dir:
        dummy_file_path = Path(temp_dir) / "test_document.pdf"
        with open(dummy_file_path, "w") as f:
            f.write("This is a test PDF.")

        # 2. Adicionar um item e anexar o arquivo
        item = api.add_item(Item(title="Item with Attachment"))
        attachment = api.add_attachment(item.id, str(dummy_file_path))

        assert attachment is not None
        assert attachment.item_id == item.id
        assert attachment.mime_type == "application/pdf"
        assert Path(attachment.path).name == "test_document.pdf"

        # 3. Verificar se o arquivo foi copiado para o armazenamento
        storage_path = database.DB_FILE.parent / "storage" / attachment.path
        assert storage_path.exists()

        # 4. Recuperar o item e verificar se o anexo está lá
        retrieved_item = api.get_item(item.id)
        assert len(retrieved_item.attachments) == 1
        assert retrieved_item.attachments[0].id == attachment.id
        assert retrieved_item.attachments[0].path == attachment.path

        # 5. Limpeza do diretório de armazenamento
        shutil.rmtree(database.DB_FILE.parent / "storage")
