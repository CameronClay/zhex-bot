from statistics import mean
from Player import Player, MatchRes

class Team:
    DIFF_PER_TEN = 400 #PLAYER A is 10 times more likely to win for every difference of 400 points
    def __init__(self, captain):
        self.players = [captain]
        self.captain = captain
    
    @property
    def Elo(self):
        return mean((player.elo for player in self.players))

    def Ea(self, teamOther):
        return 1/(1 + pow(10, (teamOther.Elo - self.Elo) / Team.DIFF_PER_TEN))
    
    def MatchResult(self, teamOther, res):
        for player in self.players:
            player.MatchResult(self.Ea(teamOther), res)
    
    def Add(self, player):
        self.players.append(player)

    @property
    def Ids(self):
        return [player.id for player in self.players]