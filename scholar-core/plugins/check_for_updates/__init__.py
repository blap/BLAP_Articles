from .checker import UpdateCheckerPlugin

def register():
    """Função de registro que o PluginManager chama."""
    return UpdateCheckerPlugin()
