from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty

class DetailView(BoxLayout):
    """
    Um widget para exibir os detalhes completos de um item selecionado.
    """
    item_id = StringProperty('')
    title = StringProperty('Selecione um item')
    authors = StringProperty('')
    details = StringProperty('') # Para outros metadados
    attachments_text = StringProperty('')
