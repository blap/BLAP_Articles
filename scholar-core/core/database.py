# core/database.py
import duckdb
from pathlib import Path

DB_FILE = Path.home() / ".scholarcore" / "library.duckdb"

from pathlib import Path

def initialize_database():
    """Cria o schema do banco de dados se ele não existir."""
    # A criação de diretório só é necessária para bancos de dados baseados em arquivo.
    if isinstance(DB_FILE, Path):
        DB_FILE.parent.mkdir(exist_ok=True)

    con = duckdb.connect(str(DB_FILE))

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

    # ... outras tabelas como 'collections', 'attachments', 'tags' ...

    con.close()

def get_connection():
    """Retorna uma conexão com o banco de dados."""
    return duckdb.connect(str(DB_FILE))
