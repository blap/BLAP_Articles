#!/usr/bin/env python3

import sys
import json
import struct
from pathlib import Path

# --- Adicionar o diretório do projeto ao sys.path ---
# O script está em .../scholar-core/native_messaging/host.py
# O diretório do projeto é o pai do pai.
project_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_dir))

from core import api, database

# --- Funções de Comunicação (Native Messaging) ---

def get_message():
    """Lê uma mensagem do stdin formatada para Native Messaging."""
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        sys.exit(0)
    message_length = struct.unpack('@I', raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode('utf-8')
    return json.loads(message)

def send_message(message):
    """Envia uma mensagem para o stdout formatada para Native Messaging."""
    encoded_content = json.dumps(message).encode('utf-8')
    encoded_length = struct.pack('@I', len(encoded_content))
    sys.stdout.buffer.write(encoded_length)
    sys.stdout.buffer.write(encoded_content)
    sys.stdout.buffer.flush()

# --- Lógica Principal ---

def main():
    # Inicializar o banco de dados se necessário (a primeira chamada fará isso)
    database.initialize_database()

    while True:
        try:
            received_message = get_message()

            # A mensagem recebida deve ser o item_data
            item_id = api.add_item(received_message)

            send_message({
                "status": "success",
                "item_id": item_id,
                "message": f"Item '{received_message.get('metadata', {}).get('title')}' salvo com sucesso."
            })

        except Exception as e:
            send_message({
                "status": "error",
                "message": str(e)
            })

if __name__ == '__main__':
    main()
