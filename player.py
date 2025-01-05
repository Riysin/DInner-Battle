class PlayerNode:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.record = {"勝": 0, "負": 0, "對戰次數": 0}
        self.next = None

class PlayerLinkedList:
    def __init__(self):
        self.head = None

    def register_player(self, username, password):
        if self.find_player(username):
            return False  # 玩家已註冊
        new_player = PlayerNode(username, password)
        if not self.head:
            self.head = new_player
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_player
        return True

    def find_player(self, username):
        current = self.head
        while current:
            if current.username == username:
                return current
            current = current.next
        return None

    def authenticate_player(self, username, password):
        player = self.find_player(username)
        return player if player and player.password == password else None