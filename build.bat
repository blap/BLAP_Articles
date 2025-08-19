@echo off
rem Sair imediatamente se um comando falhar
setlocal enabledelayedexpansion

rem --- Configuração ---
set "APP_NAME=ScholarCore"
set "VERSION=1.0.0"
set "SRC_DIR=scholar-core"
set "DIST_DIR=dist\%APP_NAME%"

echo >>> 1. Executando a suíte de testes...
python run_tests.py
if %errorlevel% neq 0 (
    echo Erro ao executar os testes. Abortando.
    exit /b %errorlevel%
)
echo.

echo >>> 2. Empacotando a aplicação com PyInstaller...
pyinstaller --noconfirm --onedir --windowed ^
    --name "%APP_NAME%" ^
    --add-data "%SRC_DIR%/gui/scholar.kv;gui" ^
    "%SRC_DIR%/run.py"
if %errorlevel% neq 0 (
    echo Erro ao empacotar com PyInstaller. Abortando.
    exit /b %errorlevel%
)
echo >>> Empacotamento concluído. Arquivos em: %DIST_DIR%
echo.

echo >>> 3. Copiando arquivos adicionais para a distribuição...
echo Copiando plugins...
xcopy /E /I /Y "%SRC_DIR%\plugins" "%DIST_DIR%\plugins\"
if %errorlevel% neq 0 (
    echo Erro ao copiar os plugins. Abortando.
    exit /b %errorlevel%
)
echo >>> Cópia de arquivos adicionais concluída.
echo.

echo >>> 4. Criando o arquivo compactado final...
echo Sistema operacional Windows não suportado para criação de arquivo compactado. Pulando.
echo.

echo >>> Processo de build concluído!
echo >>> Lançamento final em: %DIST_DIR%
endlocal
