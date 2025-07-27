class Team:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.players = []

    def add_player(self, player):
        self.players.append(player)

    def get_score(self):
        return sum(1 for p in self.players if p.alive)
