from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from core import api, database
from .widgets.listitem import ListItem
from .widgets.detailview import DetailView

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
        item_data = api.get_item(item_id)
        if not item_data:
            return

        self.detail_view.item_id = str(item_data['id'])
        self.detail_view.title = item_data.get('title', 'Sem título')

        # Formatar criadores
        authors = ", ".join([f"{c.get('first_name', '')} {c.get('last_name', '')}".strip() for c in item_data['creators']])
        self.detail_view.authors = authors

        # Formatar outros metadados
        details_text = ""
        for key, value in item_data['metadata'].items():
            if key != 'title': # O título já é exibido
                details_text += f"[b]{key.capitalize()}:[/b] {value}\n"
        self.detail_view.details = details_text

    def delete_selected_item(self):
        """Exclui o item atualmente exibido na DetailView."""
        if not self.detail_view.item_id:
            return

        item_id_to_delete = int(self.detail_view.item_id)

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


class ScholarApp(App):
    def build(self):
        # Garante que o banco de dados está inicializado antes de rodar a app
        database.initialize_database()
        return ScholarCoreRoot()

if __name__ == '__main__':
    ScholarApp().run()
