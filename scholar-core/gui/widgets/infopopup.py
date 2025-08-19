from kivy.uix.popup import Popup
from kivy.properties import StringProperty

class InfoPopup(Popup):
    """
    Um popup genérico para exibir mensagens de informação, sucesso ou erro.
    """
    message = StringProperty('')
