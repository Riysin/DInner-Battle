class PlayerNode:
    def __init__(self, username, password, instagram, gender):
        self.username = username
        self.password = password
        self.instagram = instagram
        self.gender = gender
        self.record = {"勝": 0, "負": 0, "對戰次數": 0}

class Node:
    def __init__(self):
        self.keys = []  # 儲存節點的鍵 (PlayerNode 資料)
        self.children = []  # 儲存子節點 (2-3-4 樹的結構)
        self.is_leaf = True  # 判斷是否為葉子節點

class PlayerTree:
    def __init__(self):
        self.root = Node()

    def register_player(self, username, password, instagram, gender):
        if self.find_player(username):
            return False  # 玩家已註冊
        player = PlayerNode(username, password, instagram, gender)
        if len(self.root.keys) == 3:  # 根節點已滿，進行分裂
            new_root = Node()
            new_root.is_leaf = False
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
        self._insert(self.root, player)
        return True

    def find_player(self, username):
        return self._search(self.root, username)

    def authenticate_player(self, username, password):
        player = self.find_player(username)
        return player if player and player.password == password else None

    def _search(self, node, username):
        i = 0
        while i < len(node.keys) and username > node.keys[i].username:
            i += 1

        if i < len(node.keys) and username == node.keys[i].username:
            return node.keys[i]

        if node.is_leaf:
            return None
        else:
            return self._search(node.children[i], username)

    def _insert(self, node, player):
        if node.is_leaf:
            self._insert_in_leaf(node, player)
        else:
            i = len(node.keys) - 1
            while i >= 0 and player.username < node.keys[i].username:
                i -= 1
            i += 1

            if len(node.children[i].keys) == 3:
                self._split_child(node, i)
                if player.username > node.keys[i].username:
                    i += 1

            self._insert(node.children[i], player)

    def _insert_in_leaf(self, node, player):
        i = len(node.keys) - 1
        while i >= 0 and player.username < node.keys[i].username:
            i -= 1
        node.keys.insert(i + 1, player)

    def _split_child(self, parent, index):
        full_node = parent.children[index]
        mid_index = len(full_node.keys) // 2
        mid_key = full_node.keys[mid_index]

        left_child = Node()
        right_child = Node()

        left_child.keys = full_node.keys[:mid_index]
        right_child.keys = full_node.keys[mid_index + 1:]

        if not full_node.is_leaf:
            left_child.children = full_node.children[:mid_index + 1]
            right_child.children = full_node.children[mid_index + 1:]
            left_child.is_leaf = right_child.is_leaf = False

        parent.keys.insert(index, mid_key)
        parent.children[index] = left_child
        parent.children.insert(index + 1, right_child)

    def print_tree(self):
        self._print_node(self.root, 0)

    def _print_node(self, node, level):
        print("  " * level + str([key.username for key in node.keys]))
        if not node.is_leaf:
            for child in node.children:
                self._print_node(child, level + 1)

def test():
    tree = PlayerTree()
    tree.register_player("alice", "password1", "@alice", "F")
    tree.print_tree()
    print()
    tree.register_player("bob", "password2", "@bob", "M")
    tree.print_tree()
    print()
    tree.register_player("charlie", "password3", "@charlie", "M")
    tree.print_tree()
    print()
    tree.register_player("david", "password4", "@david", "M")
    tree.print_tree()
    print()
    tree.register_player("eve", "password5", "@eve", "F")
    tree.print_tree()
    print()
    tree.register_player("aaa", "password6", "@aaa", "M")
    tree.print_tree()
    print()
    tree.register_player("bbb", "password7", "@bbb", "F")
    tree.print_tree()
    print()
    tree.register_player("ccc", "password8", "@ccc", "F")
    tree.print_tree()