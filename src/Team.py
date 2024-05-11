from src.Player import Player, MatchRes, Race

from __future__ import annotations
from statistics import mean

class Team:
    DIFF_PER_TEN = 400 #PLAYER A is 10 times more likely to win for every difference of 400 points
    def __init__(self, captain: Player):
        self.players = [captain]
        self.captain = captain
    
    def Elo(self, race: Race):
        return mean((player.elo[race] for player in self.players))

    def Ea(self, teamOther: Team, race: Race):
        return 1/(1 + pow(10, (teamOther.Elo(Race.Invert(race)) - self.Elo(race)) / Team.DIFF_PER_TEN))
    
    def MatchResult(self, teamOther: Team, race: Race, res: MatchRes):
        for player in self.players:
            player.MatchResult(self.Ea(teamOther, race), race, res)
    
    def Add(self, player: Player):
        self.players.append(player)
    
    def Remove(self, playerId: int):
        next(self.players.remove(player) for player in self.players if player.id == playerId)

    @property
    def Ids(self):
        return [player.id for player in self.players]