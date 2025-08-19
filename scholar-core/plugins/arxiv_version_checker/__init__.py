from .checker import ArxivVersionChecker

def register():
    """Função de registro que o PluginManager chama."""
    return ArxivVersionChecker()
