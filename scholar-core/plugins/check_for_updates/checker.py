# plugins/check_for_updates/checker.py
import requests
from core import api # Plugins podem usar a API do core

class PluginBase:
    """Uma classe base opcional para garantir a interface."""
    def get_name(self):
        raise NotImplementedError

class UpdateCheckerPlugin(PluginBase):
    def get_name(self):
        return "Article Update Checker"

    def setup(self, app_gui):
        """
        Método para adicionar elementos à GUI, como um botão de menu de contexto.
        Esta é a parte mais complexa, pois requer acoplar à GUI.
        """
        print(f"Plugin '{self.get_name()}' configurado.")
        # Aqui, você adicionaria um item ao menu de contexto da lista de itens da GUI.
        # Ex: app_gui.item_list.add_context_menu_item("Verificar Atualizações", self.check_selected_item)

    def check_item_update(self, item_id: int):
        """A lógica principal do plugin."""
        item_data = api.get_item(item_id) # Usa a API para pegar dados do item
        doi = item_data.get('metadata', {}).get('doi')

        if not doi:
            print("Item não possui DOI para verificação.")
            return

        print(f"Verificando atualizações para o DOI: {doi}...")

        try:
            # Usa a API do CrossRef como exemplo
            response = requests.get(f"https://api.crossref.org/works/{doi}")
            response.raise_for_status()
            crossref_data = response.json()['message']

            # 'indexed' é a data que o CrossRef processou o item
            indexed_date = crossref_data.get('indexed', {}).get('date-time')

            # Compara com a data de modificação no banco local
            # Se a data do CrossRef for mais recente, há uma possível atualização
            # ... Lógica de comparação e notificação ao usuário ...
            print(f"Data do CrossRef: {indexed_date}")

        except requests.RequestException as e:
            print(f"Erro ao contatar a API do CrossRef: {e}")

    # --- Hook Implementations ---
    def on_item_added(self, item_id: int):
        print(f"Plugin '{self.get_name()}' foi notificado que o item {item_id} foi adicionado.")
        # Poderia, por exemplo, verificar automaticamente a atualização aqui
        # self.check_item_update(item_id)

    def on_item_updated(self, item_id: int):
        print(f"Plugin '{self.get_name()}' foi notificado que o item {item_id} foi atualizado.")

    def on_item_deleted(self, item_id: int):
        print(f"Plugin '{self.get_name()}' foi notificado que o item {item_id} foi deletado.")
