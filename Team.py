from statistics import mean
from Player import Player, MatchRes, Race

class Team:
    DIFF_PER_TEN = 400 #PLAYER A is 10 times more likely to win for every difference of 400 points
    def __init__(self, captain):
        self.players = [captain]
        self.captain = captain
    
    def Elo(self, race):
        return mean((player.elo[race] for player in self.players))

    def Ea(self, teamOther, race):
        return 1/(1 + pow(10, (teamOther.Elo(Race.Invert(race)) - self.Elo(race)) / Team.DIFF_PER_TEN))
    
    def MatchResult(self, teamOther, race, res):
        for player in self.players:
            player.MatchResult(self.Ea(teamOther, race), race, res)
    
    def Add(self, player):
        self.players.append(player)

    @property
    def Ids(self):
        return [player.id for player in self.players]