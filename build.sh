#!/bin/bash

# Sair imediatamente se um comando falhar
set -e

# --- Configuração ---
APP_NAME="ScholarCore"
VERSION="1.0.0"
# O diretório que contém o código principal
SRC_DIR="scholar-core"

echo ">>> 1. Executando a suíte de testes..."
python3 -m pytest "$SRC_DIR/"
echo ">>> Testes concluídos com sucesso."
echo

echo ">>> 2. Empacotando a aplicação com PyInstaller..."
# --onedir: cria uma pasta com todas as dependências
# --windowed: no Windows/Mac, não abre um console
# --name: nome do executável e da pasta de distribuição
# --add-data: Kivy precisa que seus arquivos de dados sejam incluídos.
# O spec path é o caminho para o .spec file, que pyinstaller cria.
# PyInstaller usa ';' como separador de caminhos no Windows e ':' no resto.
path_sep=":"
if [[ "$OSTYPE" == "win32" || "$OSTYPE" == "msys" ]]; then
    path_sep=";"
fi

pyinstaller --noconfirm --onedir --windowed \
    --name "$APP_NAME" \
    --add-data "${SRC_DIR}/gui/scholar.kv${path_sep}gui" \
    "$SRC_DIR/run.py"

echo ">>> Empacotamento concluído. Arquivos em: dist/$APP_NAME"
echo

echo ">>> 3. Copiando arquivos adicionais para a distribuição..."
DIST_DIR="dist/$APP_NAME"

# Copiar o diretório de plugins
echo "Copiando plugins..."
cp -r "${SRC_DIR}/plugins" "$DIST_DIR/"

# A pasta de dados será criada pela aplicação na primeira execução,
# então não precisamos copiá-la.

echo ">>> Cópia de arquivos adicionais concluída."
echo

echo ">>> 4. Criando o arquivo compactado final..."
# Determinar o nome do arquivo com base no SO
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TAG="linux-x64"
    ARCHIVE_NAME="${APP_NAME}_v${VERSION}_${OS_TAG}.tar.gz"
    tar -czf "$ARCHIVE_NAME" -C "dist/" "$APP_NAME"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TAG="macos-x64"
    ARCHIVE_NAME="${APP_NAME}_v${VERSION}_${OS_TAG}.zip"
    zip -r "$ARCHIVE_NAME" "dist/$APP_NAME"
else
    echo "Sistema operacional não suportado para criação de arquivo. Pulando."
    ARCHIVE_NAME="dist/$APP_NAME" # fallback
fi

echo ">>> Processo de build concluído!"
echo ">>> Lançamento final: $ARCHIVE_NAME"
