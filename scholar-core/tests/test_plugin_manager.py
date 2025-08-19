import pytest
from unittest.mock import patch, MagicMock, call
from core.plugin_manager import PluginManager

# We patch the names in the 'core.plugin_manager' namespace, which is where they are looked up.

# Mock Plugin Classes
class MockPluginGood:
    def get_name(self):
        return "Good Plugin"
    def setup(self, app_gui):
        app_gui.setup_called = True
    def on_item_added(self, item_id):
        pass
    def on_item_updated(self, item_id):
        pass
    def on_item_deleted(self, item_id):
        pass
    def check_all_items(self):
        pass

@pytest.fixture
def mock_pkgutil():
    """Fixture to mock pkgutil.iter_modules."""
    mock_iter = [
        (None, 'plugins.good', None),
        (None, 'plugins.bad', None),
        (None, 'plugins.not_a_plugin', None)
    ]
    with patch('core.plugin_manager.pkgutil.iter_modules', return_value=mock_iter) as mock:
        yield mock

@pytest.fixture
def mock_importlib():
    """Fixture to mock importlib.import_module."""
    def import_side_effect(module_name):
        if module_name == 'plugins.good':
            mock_module = MagicMock()
            mock_module.register.return_value = MockPluginGood()
            return mock_module
        elif module_name == 'plugins.bad':
            mock_module = MagicMock()
            mock_module.register.side_effect = Exception("Plugin failed to load")
            return mock_module
        elif module_name == 'plugins.not_a_plugin':
            mock_module = MagicMock()
            del mock_module.register
            return mock_module
        # This allows other imports like 'plugins' itself to work
        return __import__(module_name, fromlist=[''])

    with patch('core.plugin_manager.importlib.import_module', side_effect=import_side_effect) as mock:
        yield mock

def test_plugin_discovery(mock_pkgutil, mock_importlib):
    """
    Test that the PluginManager correctly discovers and loads plugins,
    and handles failures gracefully.
    """
    manager = PluginManager()

    mock_pkgutil.assert_called_once()

    assert mock_importlib.call_count == 3
    mock_importlib.assert_has_calls([
        call('plugins.good'),
        call('plugins.bad'),
        call('plugins.not_a_plugin')
    ], any_order=True)

    assert len(manager.plugins) == 1
    assert isinstance(manager.plugins[0], MockPluginGood)

def test_hooks_are_called(mock_pkgutil, mock_importlib):
    """Test that the hooks on a loaded plugin are called correctly."""
    manager = PluginManager()
    plugin = manager.plugins[0]

    plugin.on_item_added = MagicMock()
    plugin.on_item_updated = MagicMock()
    plugin.on_item_deleted = MagicMock()

    manager.hook_item_added(10)
    plugin.on_item_added.assert_called_once_with(10)

    manager.hook_item_updated(20)
    plugin.on_item_updated.assert_called_once_with(20)

    manager.hook_item_deleted(30)
    plugin.on_item_deleted.assert_called_once_with(30)

def test_gui_and_background_hooks(mock_pkgutil, mock_importlib):
    """Test the setup and check_all_items hooks."""
    manager = PluginManager()
    plugin = manager.plugins[0]

    plugin.setup = MagicMock()
    plugin.check_all_items = MagicMock()

    mock_gui = MagicMock()
    manager.initialize_gui(mock_gui)
    plugin.setup.assert_called_once_with(mock_gui)

    manager.run_background_checks()
    plugin.check_all_items.assert_called_once()

@patch('core.plugin_manager.pkgutil.iter_modules', return_value=[])
def test_no_plugins_found(mock_iter_modules):
    """Test that the manager works correctly when no plugins are found."""
    with patch('core.plugin_manager.importlib.import_module') as mock_import_module:
        manager = PluginManager()
        assert len(manager.plugins) == 0
        # Assert that we didn't try to import any modules with 'plugins.' prefix
        for call_obj in mock_import_module.call_args_list:
            module_name = call_obj[0][0]
            assert not module_name.startswith('plugins.')

@patch('builtins.print')
def test_plugin_directory_not_found(mock_print):
    """
    Test the case where the 'plugins' module is not a package.
    """
    with patch('core.plugin_manager.plugins') as mock_plugins_pkg:
        # A non-package module won't have a __path__ attribute.
        del mock_plugins_pkg.__path__

        manager = PluginManager()

        assert len(manager.plugins) == 0
        mock_print.assert_any_call("Diretório de plugins não encontrado.")
