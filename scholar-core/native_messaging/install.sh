#!/bin/bash

# Identificar o nome do host a partir do nome do arquivo .json
HOST_NAME="com.my_company.scholarcore"

# Obter o caminho absoluto para o diretório do script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HOST_SCRIPT_PATH="$DIR/host.py"

# Determinar o diretório de destino do manifesto do Chrome
# Suporte para Chrome e Chromium no Linux
if [ "$(uname -s)" == "Linux" ]; then
    if [ -d "$HOME/.config/google-chrome/NativeMessagingHosts" ]; then
        TARGET_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
    elif [ -d "$HOME/.config/chromium/NativeMessagingHosts" ]; then
        TARGET_DIR="$HOME/.config/chromium/NativeMessagingHosts"
    else
        echo "Não foi possível encontrar o diretório NativeMessagingHosts para Chrome ou Chromium."
        exit 1
    fi
elif [ "$(uname -s)" == "Darwin" ]; then
    TARGET_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
else
    echo "Sistema operacional não suportado."
    exit 1
fi

# Criar o diretório de destino se ele não existir
mkdir -p "$TARGET_DIR"

# Substituir o placeholder do caminho no arquivo de manifesto e salvar no destino
# Usando sed para a substituição. O caractere | é usado como delimitador para evitar conflitos com /
sed "s|__PATH__|$HOST_SCRIPT_PATH|g" "$DIR/$HOST_NAME.json" > "$TARGET_DIR/$HOST_NAME.json"

# Tornar o script host executável
chmod +x "$HOST_SCRIPT_PATH"

echo "Host de Mensagens Nativas '$HOST_NAME' instalado com sucesso em '$TARGET_DIR'."
