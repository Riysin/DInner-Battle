from queue import Queue

class MatchQueue:
    def __init__(self):
        self.queue = Queue()

    def add_player(self, player):
        self.queue.put(player)

    def get_next_match(self):
        if self.queue.qsize() >= 2:
            return self.queue.get(), self.queue.get()
        return None, None