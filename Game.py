from Team import Team
from enum import Enum
from copy import deepcopy

class State(Enum):
    ZERG_PICK = 0,
    TERRAN_PICK = 1,
    IN_GAME = 2

class Game:
    TERRAN_PICK = 2
    ZERG_PICK = 1

    def __init__(self, region, playerPool):
        self.region = region
        self.state = State.ZERG_PICK
        self.playerPool = deepcopy(playerPool)
        self.zergCapt = self.ChooseCaptain()
        self.terranCapt = self.ChooseCaptain()
        self.zerg = Team(self.zergCapt)
        self.terran = Team(self.terranCapt)
        self.pickedCnt = 0

    def ChooseCaptain(self):
        player = self.playerPool[0]
        self.playerPool.remove(player)

        return player

    def PickPlayer(self, player):
        assert self.state == State.IN_GAME, "Cannot pick player while playing"
        assert len(self.playerPool) == 0, "Cannot pick player from empty pool"
        assert player not in self.playerPool, "Player not currently playing"

        if self.state == State.ZERG_PICK:
            self.zerg.Add(player)
        elif self.state == State.TERRAN_PICK:
            self.terran.Add(player)
        else:
            raise AssertionError("Cannot pick player in this state")

        self.playerPool.remove(player)

        if len(self.playerPool) == 0:
            self.state = State.IN_GAME
        else:
            self.ChangeTurn()

    def ChangeTurn(self):
        if (self.pickedCnt == State.TERRAN_PICK) and (self.state == State.TERRAN_PICK):
            self.state = State.ZERG_PICK
        else:
            self.state = State.TERRAN_PICK

        self.pickedCnt += 1

    def CaptOnTeam(self, player):
        return self.zergCapt == player or self.terranCapt == player
    
    def CaptRace(self, player):
        if self.zergCapt == player:
            return "Zerg"
        if self.terranCapt == player:
            return "Terran"
        else:
            raise AssertionError(f"{player} must be a captain")