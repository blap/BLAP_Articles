from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.app import App
from core import api

class CollectionNode(TreeViewLabel):
    collection_id = ObjectProperty(None, allownone=True)

class CollectionsTree(TreeView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))
        self.hide_root = True
        self.bind(selected_node=self.on_node_select)
        Clock.schedule_once(self.populate_tree)

    def on_node_select(self, instance, value):
        """Chamado quando um nó da árvore é selecionado."""
        if value and hasattr(value, 'collection_id'):
            collection_id = value.collection_id
            App.get_running_app().root.load_items(collection_id=collection_id)

    def populate_tree(self, dt=None):
        for node in list(self.iterate_all_nodes()):
            self.remove_node(node)

        # Adicionar um nó "Todas as Publicações"
        all_items_node = CollectionNode(text="Todas as Publicações", collection_id=None)
        self.add_node(all_items_node)

        collections = api.get_all_collections()
        nodes = {}

        for collection in collections:
            if collection.parent_id is None:
                node = CollectionNode(text=collection.name, collection_id=collection.id)
                self.add_node(node)
                nodes[collection.id] = node

        for collection in collections:
            if collection.parent_id is not None and collection.parent_id in nodes:
                parent_node = nodes[collection.parent_id]
                node = CollectionNode(text=collection.name, collection_id=collection.id)
                self.add_node(node, parent_node)
                nodes[collection.id] = node
