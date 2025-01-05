class GameLogic:
    @staticmethod
    def judge_winner(symbol1, symbol2):
        rules = {"剪刀": "布", "布": "石頭", "石頭": "剪刀"}
        if symbol1 == symbol2:
            return "平手", "平手"
        elif rules[symbol1] == symbol2:
            return "勝利", "失敗"
        else:
            return "失敗", "勝利"