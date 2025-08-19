from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty

class ListItem(BoxLayout):
    """
    Um widget para exibir um único item na lista principal.
    """
    item_id = NumericProperty(0)
    title = StringProperty('')
    author_text = StringProperty('')

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            from kivy.app import App
            # Chama o método no widget raiz para mostrar os detalhes
            App.get_running_app().root.show_details_for_item(self.item_id)
            return super().on_touch_down(touch)
        return False
