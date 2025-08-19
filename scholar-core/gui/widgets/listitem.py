from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior

class ListItem(RecycleDataViewBehavior, BoxLayout):
    """
    Um widget para exibir um único item na lista principal, compatível com RecycleView.
    """
    item_id = NumericProperty(0)
    title = StringProperty('')
    author_text = StringProperty('')
    update_available = BooleanProperty(False)

    # Propriedade para o estado de seleção
    selected = BooleanProperty(False)

    def refresh_view_attrs(self, rv, index, data):
        """ Pega os dados do RecycleView e os aplica às propriedades do widget. """
        self.item_id = data.get('item_id', 0)
        self.title = data.get('title', '')
        self.author_text = data.get('author_text', '')
        self.update_available = data.get('update_available', False)
        return super(ListItem, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        """ Adiciona o comportamento de seleção ao toque. """
        if super(ListItem, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos):
            from kivy.app import App
            App.get_running_app().root.show_details_for_item(self.item_id)
            return True
        return False

    def apply_selection(self, rv, index, is_selected):
        """ Responde à mudança de seleção. """
        self.selected = is_selected
