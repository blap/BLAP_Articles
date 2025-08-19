from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from core import api, database
from .widgets.listitem import ListItem
from .widgets.detailview import DetailView
from .widgets.infopopup import InfoPopup
import traceback

class ScholarCoreRoot(BoxLayout):
    item_list = ObjectProperty(None)
    detail_view = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Adiar o carregamento para garantir que a UI esteja pronta
        Clock.schedule_once(self.load_items)

    def load_items(self, dt=None):
        """Carrega os resumos dos itens e popula a lista na GUI."""
        summaries = api.get_all_items_summary()
        self.item_list.clear_widgets()
        for summary in summaries:
            list_item = ListItem(
                item_id=summary['id'],
                title=summary['title'] or "Sem título",
                author_text=summary['author_text']
            )
            self.item_list.add_widget(list_item)

    def show_details_for_item(self, item_id):
        """Busca os detalhes de um item e atualiza a DetailView."""
        item = api.get_item(item_id)
        if not item:
            return

        self.detail_view.item_id = str(item.id)
        self.detail_view.title = item.title or 'Sem título'

        # Formatar criadores
        authors = ", ".join([f"{c.first_name or ''} {c.last_name or ''}".strip() for c in item.creators])
        self.detail_view.authors = authors

        # Formatar outros metadados
        details_text = ""
        for key, value in item.metadata.items():
            if key.lower() != 'title': # O título já é exibido
                details_text += f"[b]{key.capitalize()}:[/b] {value}\n"
        self.detail_view.details = details_text

        # Formatar anexos
        attachments_text = "\n".join([att.path for att in item.attachments])
        self.detail_view.attachments_text = attachments_text

    def show_popup(self, message, title="Aviso"):
        """Exibe um popup com uma mensagem."""
        popup = InfoPopup(message=message, title=title)
        popup.open()

    def delete_selected_item(self):
        """Exclui o item atualmente exibido na DetailView."""
        if not self.detail_view.item_id:
            return

        item_id_to_delete = int(self.detail_view.item_id)

        try:
            # Chamar a API do Core
            success = api.delete_item(item_id_to_delete)

            if success:
                # Limpar a DetailView
                self.detail_view.item_id = ''
                self.detail_view.title = 'Selecione um item'
                self.detail_view.authors = ''
                self.detail_view.details = ''

                # Recarregar a lista de itens
                self.load_items()
                self.show_popup("Item excluído com sucesso.", "Sucesso")
            else:
                # Isso não deveria acontecer se o item_id for válido
                self.show_popup("Não foi possível excluir o item.", "Erro")
        except Exception as e:
            self.show_popup(f"Ocorreu um erro:\n{e}\n\n{traceback.format_exc()}", "Erro de Exclusão")


class ScholarApp(App):
    def build(self):
        # Garante que o banco de dados está inicializado antes de rodar a app
        database.initialize_database()

        # Cria a instância do widget raiz
        root_widget = ScholarCoreRoot()

        # Conecta os plugins à GUI
        from core.plugin_manager import manager as plugin_manager
        plugin_manager.initialize_gui(root_widget)

        return root_widget

if __name__ == '__main__':
    ScholarApp().run()
