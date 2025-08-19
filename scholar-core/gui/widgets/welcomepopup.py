from kivy.uix.popup import Popup
from kivy.properties import StringProperty

class WelcomePopup(Popup):
    """
    Um popup para ser exibido na primeira execução da aplicação.
    """
    data_path = StringProperty('')
