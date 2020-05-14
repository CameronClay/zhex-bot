from statistics import mean
from Player import Player

class Team:
    def __init__(self, captain):
        self.players = [captain]
        self.captain = captain
    
    @property
    def Elo(self):
        return mean(self.players)

    @property
    def Ea(self, TeamOther):
        return 1/(1 + pow(10, (self.Elo - TeamOther.Elo)/ 400))
    
    def MatchResult(self, ea, res):
        for player in self.players:
            player.MatchResult(self.Ea, res)
    
    def Add(self, player):
        self.players.append(player)