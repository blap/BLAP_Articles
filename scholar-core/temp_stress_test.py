import sys
import os
from pathlib import Path

# Adiciona o diretório do projeto ao path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

from core import api, database
from core.models import Item, Creator

def run_stress_test(num_items):
    print(f"Iniciando teste de estresse: populando o banco com {num_items} itens...")

    # Garantir que estamos usando o banco de dados portátil
    if os.path.exists(database.DB_FILE):
        os.remove(database.DB_FILE)
    database.initialize_database()

    for i in range(num_items):
        item = Item(
            item_type="journalArticle",
            title=f"Artigo de Teste Número {i}",
            creators=[Creator(first_name="Autor", last_name=str(i))]
        )
        api.add_item(item)
        if (i + 1) % 500 == 0:
            print(f"Adicionados {i + 1}/{num_items} itens...")

    print("População do banco de dados concluída.")

if __name__ == "__main__":
    # Reduzindo para um número pequeno para depuração rápida
    run_stress_test(50)
