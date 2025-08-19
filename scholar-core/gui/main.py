from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from core import api, database
from .widgets.listitem import ListItem
from .widgets.detailview import DetailView
from .widgets.infopopup import InfoPopup
from .widgets.collectionstree import CollectionsTree
from .widgets.welcomepopup import WelcomePopup
import traceback
import threading
import os

class ScholarCoreRoot(BoxLayout):
    item_list = ObjectProperty(None)
    detail_view = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.load_items)

    def load_items(self, dt=None, collection_id=None):
        try:
            if collection_id is None:
                summaries = api.get_all_items_summary()
            else:
                summaries = api.get_items_in_collection(collection_id)

            # Formatar dados para o RecycleView
            self.item_list.data = [{
                'item_id': s['id'],
                'title': s['title'] or "Sem título",
                'author_text': s['author_text'],
                'update_available': False # O estado inicial é sem atualização
            } for s in summaries]

            self.item_list.refresh_from_data()
            self.trigger_background_checks()
        except Exception as e:
            self.show_popup(f"Falha ao carregar itens:\n{e}", "Erro de Banco de Dados")

    def show_details_for_item(self, item_id):
        try:
            item = api.get_item(item_id)
            if not item:
                self.show_popup(f"Não foi possível encontrar o item com ID: {item_id}", "Erro")
                return

            self.detail_view.item_id = str(item.id)
            self.detail_view.title = item.title or 'Sem título'

            authors = ", ".join([f"{c.first_name or ''} {c.last_name or ''}".strip() for c in item.creators])
            self.detail_view.authors = authors

            details_text = ""
            for key, value in item.metadata.items():
                if key.lower() != 'title':
                    details_text += f"[b]{key.capitalize()}:[/b] {value}\n"
            self.detail_view.details = details_text

            attachments_text = "\n".join([att.path for att in item.attachments])
            self.detail_view.attachments_text = attachments_text
        except Exception as e:
            self.show_popup(f"Falha ao buscar detalhes do item:\n{e}", "Erro")

    def trigger_background_checks(self):
        from core.plugin_manager import manager as plugin_manager
        threading.Thread(target=plugin_manager.run_background_checks).start()

    def mark_items_as_updatable(self, item_ids: list):
        """Atualiza a UI para marcar itens que têm uma atualização disponível."""
        # A alteração precisa ser feita nos dados, não nos widgets filhos.
        for item_data in self.item_list.data:
            if item_data['item_id'] in item_ids:
                item_data['update_available'] = True
            else:
                # Garantir que o estado seja resetado se não houver mais atualização
                item_data['update_available'] = False

        # Forçar a atualização da view a partir dos dados modificados
        self.item_list.refresh_from_data()

    def show_popup(self, message, title="Aviso"):
        popup = InfoPopup(message=message, title=title)
        popup.open()

    def delete_selected_item(self):
        if not self.detail_view.item_id:
            return
        item_id_to_delete = int(self.detail_view.item_id)
        try:
            success = api.delete_item(item_id_to_delete)
            if success:
                self.detail_view.item_id = ''
                self.detail_view.title = 'Selecione um item'
                self.detail_view.authors = ''
                self.detail_view.details = ''
                self.load_items()
                self.show_popup("Item excluído com sucesso.", "Sucesso")
            else:
                self.show_popup("Não foi possível excluir o item.", "Erro")
        except Exception as e:
            self.show_popup(f"Ocorreu um erro:\n{e}\n\n{traceback.format_exc()}", "Erro de Exclusão")

class ScholarApp(App):
    def build(self):
        # Retorna um widget placeholder para a janela ser criada
        return BoxLayout()

    def on_start(self):
        if not os.path.exists(database.DB_FILE):
            popup = WelcomePopup(data_path=database.DATA_DIR)
            popup.bind(on_dismiss=self.build_main_ui)
            popup.open()
        else:
            self.build_main_ui()

    def build_main_ui(self, *args):
        """Constrói e inicializa a interface principal do usuário."""
        self.root.clear_widgets() # Limpa o placeholder

        database.initialize_database()
        root_widget = ScholarCoreRoot()
        from core.plugin_manager import manager as plugin_manager
        plugin_manager.initialize_gui(root_widget)

        self.root.add_widget(root_widget)

if __name__ == '__main__':
    ScholarApp().run()
