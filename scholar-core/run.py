import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path para que os módulos possam ser encontrados
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from gui.main import ScholarApp

if __name__ == '__main__':
    ScholarApp().run()
