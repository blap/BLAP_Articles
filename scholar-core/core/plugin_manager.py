import importlib
import pkgutil
import plugins

class PluginManager:
    def __init__(self):
        self.plugins = []
        self._discover_plugins()

    def _discover_plugins(self):
        """Encontra e carrega plugins do diretório 'plugins'."""
        print("Descobrindo plugins...")
        # Certifique-se de que o diretório de plugins exista
        if not hasattr(plugins, '__path__'):
            print("Diretório de plugins não encontrado.")
            return

        for _, name, _ in pkgutil.iter_modules(plugins.__path__, prefix='plugins.'):
            try:
                module = importlib.import_module(name)
                if hasattr(module, 'register'):
                    plugin_instance = module.register()
                    self.plugins.append(plugin_instance)
                    print(f"Plugin '{name}' carregado.")
            except Exception as e:
                print(f"Falha ao carregar o plugin {name}: {e}")

    def hook_item_added(self, item_id: int):
        """Hook chamado quando um item é adicionado."""
        print(f"Hook: Item {item_id} adicionado.")
        for plugin in self.plugins:
            if hasattr(plugin, 'on_item_added'):
                plugin.on_item_added(item_id)

    def hook_item_updated(self, item_id: int):
        """Hook chamado quando um item é atualizado."""
        print(f"Hook: Item {item_id} atualizado.")
        for plugin in self.plugins:
            if hasattr(plugin, 'on_item_updated'):
                plugin.on_item_updated(item_id)

    def hook_item_deleted(self, item_id: int):
        """Hook chamado quando um item é deletado."""
        print(f"Hook: Item {item_id} deletado.")
        for plugin in self.plugins:
            if hasattr(plugin, 'on_item_deleted'):
                plugin.on_item_deleted(item_id)

    def initialize_gui(self, app_gui):
        """
        Fornece aos plugins uma referência à instância da GUI para que possam
        adicionar elementos de UI, etc.
        """
        print("Inicializando plugins na GUI...")
        for plugin in self.plugins:
            if hasattr(plugin, 'setup'):
                plugin.setup(app_gui)

# Instância global única do gerenciador de plugins
manager = PluginManager()
