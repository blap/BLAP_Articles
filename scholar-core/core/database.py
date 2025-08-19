# core/database.py
import duckdb
import os
import sys

# Determina o diretório base da aplicação
if getattr(sys, 'frozen', False):
    # Se estiver rodando como um executável empacotado
    application_path = os.path.dirname(sys.executable)
else:
    # Se estiver rodando como um script .py normal
    # __file__ é .../scholar-core/core/database.py, então precisamos de dois .parent
    application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define o caminho para o diretório de dados e o arquivo do banco de dados
DATA_DIR = os.path.join(application_path, 'data')
DB_FILE = os.path.join(DATA_DIR, 'library.duckdb')


def initialize_database():
    """Cria o schema do banco de dados se ele não existir."""
    # A criação de diretório só é necessária para bancos de dados baseados em arquivo.
    # O teste usará um caminho em branco, então verifique se DB_FILE não está vazio.
    if DB_FILE:
        db_dir = os.path.dirname(DB_FILE)
        os.makedirs(db_dir, exist_ok=True)

    con = duckdb.connect(DB_FILE)

    # Tabela principal para itens bibliográficos
    con.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id BIGINT PRIMARY KEY,
        item_type VARCHAR(50) NOT NULL, -- ex: 'journalArticle', 'book'
        title TEXT,
        date_added TIMESTAMP DEFAULT current_timestamp,
        date_modified TIMESTAMP DEFAULT current_timestamp
    );
    """)

    # Tabela para metadados (chave-valor)
    con.execute("""
    CREATE TABLE IF NOT EXISTS metadata (
        item_id BIGINT,
        field VARCHAR(100),
        value TEXT,
        PRIMARY KEY (item_id, field),
        FOREIGN KEY (item_id) REFERENCES items(id)
    );
    """)

    # Criadores (autores, editores, etc.)
    con.execute("""
    CREATE TABLE IF NOT EXISTS creators (
        id BIGINT PRIMARY KEY,
        first_name VARCHAR,
        last_name VARCHAR
    );
    """)

    # Tabela de junção para itens e criadores
    con.execute("""
    CREATE TABLE IF NOT EXISTS item_creators (
        item_id BIGINT,
        creator_id BIGINT,
        creator_type VARCHAR(50), -- ex: 'author', 'editor'
        order_index INTEGER,
        PRIMARY KEY (item_id, creator_id, creator_type),
        FOREIGN KEY (item_id) REFERENCES items(id),
        FOREIGN KEY (creator_id) REFERENCES creators(id)
    );
    """)

    # Tabela para tags
    con.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        id BIGINT PRIMARY KEY,
        name VARCHAR UNIQUE NOT NULL
    );
    """)

    # Tabela de junção para itens e tags
    con.execute("""
    CREATE TABLE IF NOT EXISTS item_tags (
        item_id BIGINT,
        tag_id BIGINT,
        PRIMARY KEY (item_id, tag_id),
        FOREIGN KEY (item_id) REFERENCES items(id),
        FOREIGN KEY (tag_id) REFERENCES tags(id)
    );
    """)

    # Tabela para coleções
    con.execute("""
    CREATE TABLE IF NOT EXISTS collections (
        id BIGINT PRIMARY KEY,
        name VARCHAR NOT NULL,
        parent_id BIGINT,
        FOREIGN KEY (parent_id) REFERENCES collections(id)
    );
    """)

    # Tabela de junção para itens e coleções
    con.execute("""
    CREATE TABLE IF NOT EXISTS item_collections (
        item_id BIGINT,
        collection_id BIGINT,
        PRIMARY KEY (item_id, collection_id),
        FOREIGN KEY (item_id) REFERENCES items(id),
        FOREIGN KEY (collection_id) REFERENCES collections(id)
    );
    """)

    # Tabela para anexos
    con.execute("""
    CREATE TABLE IF NOT EXISTS attachments (
        id BIGINT PRIMARY KEY,
        item_id BIGINT,
        path TEXT NOT NULL,
        mime_type VARCHAR,
        date_added TIMESTAMP DEFAULT current_timestamp,
        FOREIGN KEY (item_id) REFERENCES items(id)
    );
    """)

    con.close()

def get_connection():
    """Retorna uma conexão com o banco de dados."""
    return duckdb.connect(str(DB_FILE))
