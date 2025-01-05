class RestaurantNode:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.left = None
        self.right = None

class RestaurantBST:
    def __init__(self):
        self.root = None

    def add_restaurant(self, name, symbol):
        new_node = RestaurantNode(name, symbol)
        if not self.root:
            self.root = new_node
        else:
            self._insert(self.root, new_node)

    def _insert(self, current, new_node):
        if new_node.name < current.name:
            if current.left:
                self._insert(current.left, new_node)
            else:
                current.left = new_node
        elif new_node.name > current.name:
            if current.right:
                self._insert(current.right, new_node)
            else:
                current.right = new_node

    def search(self, name):
        return self._search(self.root, name)

    def _search(self, current, name):
        if not current:
            return None
        if current.name == name:
            return current
        elif name < current.name:
            return self._search(current.left, name)
        else:
            return self._search(current.right, name)

    def get_random_restaurant(self):
        import random
        restaurants = self._inorder_traversal(self.root)
        return random.choice(restaurants) if restaurants else None

    def _inorder_traversal(self, node):
        if not node:
            return []
        return self._inorder_traversal(node.left) + [node] + self._inorder_traversal(node.right)
