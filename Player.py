class Player:
    AMOUNT = 50
    def __init__(self):
        self.wins = 0
        self.loses = 0
        self.elo = 1500

    @property 
    def Games(self):
        return self.wins + self.loses

    @property
    def Ratio(self):
        return float(self.wins) / self.loses

    def MatchResult(self, ea, res):
        k = 25 if self.Games < 30 else 15
        self.elo = self.elo + k * (res - ea)