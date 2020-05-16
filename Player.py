from enum import IntEnum
from datetime import date
class MatchRes(IntEnum):
    WIN = 1,
    LOSS = 0,
    TIE = 2

class Player:
    AMOUNT = 50
    def __init__(self, id, region, wins = 0, loses = 0, games = 0, elo = 1500, lastPlayed = None):
        self.id = id
        self.region = region
        self.wins = wins
        self.loses = loses
        self.games = games
        self.elo = elo
        self.lastPlayed = lastPlayed

    @property
    def Ratio(self):
        return float(self.wins) / self.loses

    def MatchResult(self, ea, res : MatchRes):
        k = 25 if self.games < 30 else 15
        self.elo = max(self.elo + k * (int(res) - ea), 0)
        self.lastPlayed = date.today()

        if res == MatchRes.WIN:
            self.wins += 1
        elif res == MatchRes.LOSS:
            self.loses += 1

        self.games += 1