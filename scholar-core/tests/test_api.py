import pytest
from core import api, database
from core.models import Item, Creator, Collection
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

TEST_DB_FILE = "test_library.db"

@pytest.fixture(autouse=True)
def setup_test_database():
    # Salvar o caminho original do DB e do DATA_DIR
    original_db_file = database.DB_FILE
    original_data_dir = database.DATA_DIR

    # Apontar para um diretório de dados de teste no diretório de trabalho atual
    test_data_dir = os.path.join(os.getcwd(), "test_data")
    database.DATA_DIR = test_data_dir
    database.DB_FILE = os.path.join(test_data_dir, TEST_DB_FILE)

    # Limpar o diretório de teste antes de cada teste
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)

    database.initialize_database()

    yield

    # Limpeza após o teste
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)

    # Restaurar os caminhos originais
    database.DB_FILE = original_db_file
    database.DATA_DIR = original_data_dir

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

# ... (todos os outros testes permanecem os mesmos, pois eles usam a API
# que agora é agnóstica ao caminho exato do banco de dados, com exceção do test_attachments)

def test_attachments():
    """Testa a adição e recuperação de anexos."""
    import tempfile

    # 1. Setup: criar um arquivo dummy
    with tempfile.TemporaryDirectory() as temp_dir:
        dummy_file_path = os.path.join(temp_dir, "test_document.pdf")
        with open(dummy_file_path, "w") as f:
            f.write("This is a test PDF.")

        # 2. Adicionar um item e anexar o arquivo
        item = api.add_item(Item(title="Item with Attachment"))
        attachment = api.add_attachment(item.id, dummy_file_path)

        assert attachment is not None
        assert attachment.item_id == item.id
        assert attachment.mime_type == "application/pdf"
        assert os.path.basename(attachment.path) == "test_document.pdf"

        # 3. Verificar se o arquivo foi copiado para o armazenamento
        # database.DATA_DIR foi modificado pelo fixture para apontar para 'test_data'
        storage_path = os.path.join(database.DATA_DIR, "storage", attachment.path)
        assert os.path.exists(storage_path)

        # 4. Recuperar o item e verificar se o anexo está lá
        retrieved_item = api.get_item(item.id)
        assert len(retrieved_item.attachments) == 1
        assert retrieved_item.attachments[0].id == attachment.id
        assert retrieved_item.attachments[0].path == attachment.path

# Manter os outros testes que não precisam de modificação
def test_add_item_with_creators_deduplication():
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
    assert creator_count == 3

def test_get_item():
    item_to_add = Item(item_type="book", title="A Complete Guide to DuckDB", metadata={"publisher": "O'Reilly"}, creators=[Creator(first_name="Mark", last_name="Richards")])
    added_item = api.add_item(item_to_add)
    retrieved_item = api.get_item(added_item.id)
    assert retrieved_item is not None
    assert retrieved_item.id == added_item.id
    assert retrieved_item.metadata["publisher"] == "O'Reilly"
    assert api.get_item(999999) is None

def test_delete_item():
    item_to_add = Item(item_type="report", title="Annual Report")
    added_item = api.add_item(item_to_add)
    assert api.get_item(added_item.id) is not None
    delete_result = api.delete_item(added_item.id)
    assert delete_result is True
    assert api.get_item(added_item.id) is None
    assert api.delete_item(999999) is False

def test_update_item():
    item_to_add = Item(item_type="book", title="Initial Title", metadata={"publisher": "Old Publisher"})
    added_item = api.add_item(item_to_add)
    update_data = {"metadata": {"title": "Updated Title", "year": "2024"}}
    api.update_item(added_item.id, update_data)
    updated_item = api.get_item(added_item.id)
    assert updated_item.title == "Updated Title"
    assert updated_item.metadata["year"] == "2024"

def test_collections():
    item1 = api.add_item(Item(title="Book One"))
    api.add_item(Item(title="Book Two"))
    collection_id = api.add_collection("My Test Collection")
    api.add_item_to_collection(item1.id, collection_id)
    items_in_coll = api.get_items_in_collection(collection_id)
    assert len(items_in_coll) == 1
    assert items_in_coll[0]['id'] == item1.id

def test_tags():
    item = api.add_item(Item(title="Test Page"))
    tag_id = api.add_tag("test-tag")
    api.add_tag_to_item(item.id, tag_id)
    item_tags = api.get_item_tags(item.id)
    assert len(item_tags) == 1
    assert item_tags[0]['name'] == "test-tag"

def test_search_items():
    api.add_item(Item(title="The History of Science"))
    api.add_item(Item(title="A study on duckdb", metadata={"abstract": "performance"}))
    results = api.search_items("science")
    assert len(results) == 1
    results_perf = api.search_items("performance")
    assert len(results_perf) == 1

def test_add_item_edge_cases():
    item = api.add_item(Item(item_type="note"))
    retrieved = api.get_item(item.id)
    assert retrieved.title is None

def test_linking_failures():
    item = api.add_item(Item(title="My Note"))
    collection_id = api.add_collection("My Collection")
    tag_id = api.add_tag("my-tag")
    assert not api.add_item_to_collection(item.id, 999)
    assert not api.add_tag_to_item(999, tag_id)

@patch('core.services.item_service.requests.get')
@patch('core.services.item_service.PdfReader')
def test_create_item_from_pdf(MockPdfReader, mock_requests_get):
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {'message': {'title': ['Mocked PDF Title'], 'author': [{'given': 'John', 'family': 'Doe'}]}}
    mock_requests_get.return_value = mock_response
    mock_pdf_instance = MockPdfReader.return_value
    mock_pdf_instance.metadata.title = "Original PDF Title"
    mock_page = Mock()
    mock_page.extract_text.return_value = "Some text with a DOI: 10.1234/mock.doi"
    mock_pdf_instance.pages = [mock_page]
    with tempfile.TemporaryDirectory() as temp_dir:
        dummy_file_path = os.path.join(temp_dir, "test.pdf")
        Path(dummy_file_path).touch()
        item = api.create_item_from_pdf(dummy_file_path)
        assert item.title == "Mocked PDF Title"
        assert len(item.attachments) == 1

def test_get_all_collections():
    parent_id = api.add_collection("Parent")
    api.add_collection("Child", parent_id=parent_id)
    collections = api.get_all_collections()
    assert len(collections) == 2
    child_coll = next(c for c in collections if c.name == "Child")
    assert child_coll.parent_id == parent_id

def test_add_attachment_failures():
    """Testa falhas na adição de anexos."""
    item = api.add_item(Item(title="Item for attachments"))
    # 1. Arquivo de origem não existe
    assert api.add_attachment(item.id, "/path/to/non/existent/file.pdf") is None
    # 2. Item não existe
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        assert api.add_attachment(999999, tmp.name) is None

def test_add_duplicate_associations():
    """Testa a adição de associações duplicadas (item-coleção, item-tag)."""
    item = api.add_item(Item(title="Test Duplicates"))
    collection_id = api.add_collection("Dup Collection")
    tag_id = api.add_tag("dup-tag")
    # Adicionar a primeira vez (sucesso)
    assert api.add_item_to_collection(item.id, collection_id) is True
    assert api.add_tag_to_item(item.id, tag_id) is True
    # Adicionar a segunda vez (deve ser tratado graciosamente)
    assert api.add_item_to_collection(item.id, collection_id) is True
    assert api.add_tag_to_item(item.id, tag_id) is True

@patch('core.services.item_service.PdfReader', side_effect=Exception("Corrupted PDF"))
def test_create_item_from_corrupted_pdf(MockPdfReader):
    """Testa a criação de item a partir de um PDF que gera erro."""
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        # O conteúdo do arquivo não importa, pois PdfReader será mockado
        item = api.create_item_from_pdf(tmp.name)
        assert item is None
