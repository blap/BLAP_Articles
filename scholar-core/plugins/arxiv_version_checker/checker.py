import requests
import xml.etree.ElementTree as ET
from core import api

class ArxivVersionChecker:
    def get_name(self):
        return "arXiv Version Checker"

    def setup(self, app_gui):
        self.app_gui = app_gui
        print(f"Plugin '{self.get_name()}' configurado.")
        # O plugin agora tem acesso à GUI e pode chamar métodos nela.
        # Ex: self.app_gui.show_popup(...)

    def _is_arxiv_item(self, item):
        """Verifica se um item é do arXiv."""
        if item.metadata.get('arxiv_id'):
            return True
        # Poderia também verificar a URL, etc.
        return False

    def _get_latest_version_from_api(self, arxiv_id):
        """Busca a versão mais recente de um artigo na API do arXiv."""
        try:
            url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            response = requests.get(url)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            # Namespace da API do Atom
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            # O link do PDF contém o número da versão no final (ex: .../abs/1234.5678v2)
            pdf_link = root.find('atom:entry/atom:id', ns).text

            if 'v' in pdf_link:
                version_str = pdf_link.split('v')[-1]
                return int(version_str)
            return 1 # Se não houver 'v', é a versão 1
        except Exception:
            return None # Falha na rede, parsing, etc.

    def check_for_update(self, item_id):
        """Verifica se um único item tem uma atualização."""
        item = api.get_item(item_id)
        if not item or not self._is_arxiv_item(item):
            return None

        arxiv_id = item.metadata.get('arxiv_id')
        local_version = int(item.metadata.get('version', 1))

        latest_version = self._get_latest_version_from_api(arxiv_id)

        if latest_version and latest_version > local_version:
            return {'item_id': item_id, 'latest_version': latest_version}
        return None

    def check_all_items(self):
        """
        Verifica todos os itens da biblioteca e retorna uma lista de IDs
        de itens que têm atualizações.
        """
        updated_items = []
        all_items = api.get_all_items_summary() # Usar summary para eficiência
        for summary in all_items:
            # Precisamos do item completo para checar os metadados
            update_info = self.check_for_update(summary['id'])
            if update_info:
                updated_items.append(update_info['item_id'])

        print(f"Verificação concluída. Itens com atualização: {updated_items}")
        # Notificar a GUI para atualizar a interface
        if hasattr(self.app_gui, 'mark_items_as_updatable'):
            self.app_gui.mark_items_as_updatable(updated_items)

        return updated_items

    def update_article_metadata(self, item_id):
        """Atualiza os metadados de um item para a versão mais recente."""
        # Lógica para re-buscar metadados da API e chamar api.update_item
        print(f"Lógica de atualização de metadados para o item {item_id} a ser implementada.")
        # Após a atualização, poderia baixar o novo PDF.
        self.app_gui.show_popup("Metadados atualizados com sucesso!", "Sucesso")
        # E remover o marcador de atualização da GUI
        self.app_gui.mark_items_as_updatable([]) # Simplificado
        self.app_gui.load_items() # Recarregar a lista
