class MatchQueue:
    def __init__(self):
        self.queue = []

    def add_player(self, player):
        self.queue.append(player)

    def get_next_match(self):
        if len(self.queue) >= 2:
            return self.queue.pop(0), self.queue.pop(0)
        return None, None