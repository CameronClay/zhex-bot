from Team import Team
from enum import Enum
from copy import deepcopy
from Player import MatchRes
import itertools

class State(Enum):
    ZERG_PICK = 0,
    TERRAN_PICK = 1,
    IN_GAME = 2

class Game:
    N_PLAYERS = 3
    TERRAN_PICK = 2
    ZERG_PICK = 1

    def __init__(self, region, playerPool):
        assert len(playerPool) == Game.N_PLAYERS

        self.region = region
        self.state = State.ZERG_PICK
        self.playerPool = deepcopy(playerPool)
        self.zergCapt = self.ChooseCaptain()
        self.terranCapt = self.ChooseCaptain()
        self.zerg = Team(self.zergCapt)
        self.terran = Team(self.terranCapt)
        self.playerTurn = self.zergCapt
        self.pickedCnt = 0

    def ChooseCaptain(self):
        player = max(self.playerPool, key=lambda player: player.elo)
        self.playerPool.remove(player)

        return player

    def __AddPlayer(self, player):  
        if self.state == State.ZERG_PICK:
            self.zerg.Add(player)
        elif self.state == State.TERRAN_PICK:
            self.terran.Add(player)
        else:
            raise AssertionError("Cannot pick player in this state")

    def __PickLastPlayer(self):
        if len(self.playerPool) == 1:
            self.PickAfk()

        if len(self.playerPool) == 0:
            self.__Start()
        else:
            self.ChangeTurn()

    def __Start(self):
         self.state = State.IN_GAME

    def PickPlayer(self, playerId):
        assert self.state != State.IN_GAME, "Cannot pick player while playing"
        assert len(self.playerPool) != 0  , "Cannot pick player from empty pool"

        matches = list(filter(lambda player: player.id == playerId, self.playerPool))
        assert len(matches) != 0, "Cannot find player to pick"
        player = matches[0]

        self.__AddPlayer(player)

        self.playerPool.remove(player)

        self.__PickLastPlayer()

    def ChangeTurn(self):
        if (self.pickedCnt == State.TERRAN_PICK) and (self.state == State.TERRAN_PICK):
            self.state = State.ZERG_PICK
            self.playerTurn = self.zergCapt
        else:
            self.state = State.TERRAN_PICK
            self.playerTurn = self.terranCapt

        self.pickedCnt += 1

    def CaptOnTeam(self, playerId):
        return self.zergCapt.id == playerId or self.terranCapt.id == playerId
    
    #get race of player
    def PlayerRace(self, playerId):
        if playerId in self.zerg.Ids:
            return "Zerg"
        elif playerId in self.terran.Ids:
            return "Terran"
        else:
            return ""

    def GetVictor(self, playerId, res):
        victor = ""
        if res == MatchRes.TIE:
            victor = "Tie"
        elif playerId in self.zerg.Ids and res == MatchRes.WIN:
            victor = "Zerg"
        else:
            victor = "Terran"
        return victor

    def MatchResult(self, captainId, res):
        notRes = MatchRes.LOSS if res == MatchRes.WIN else MatchRes.WIN

        if captainId == self.zergCapt.id:
            self.zerg.MatchResult(self.terran, res)
            self.terran.MatchResult(self.zerg, notRes)
        elif captainId == self.terranCapt.id:
            self.zerg.MatchResult(self.terran, notRes)
            self.terran.MatchResult(self.zerg, res)
        else:
            raise AssertionError(f"Must be a captain to report match")

    def PickAfk(self):
        pickedPlayer = self.playerPool.pop()
        self.__AddPlayer(pickedPlayer)
        self.__PickLastPlayer()
        return pickedPlayer
    
    def IsPlaying(self, playerId):
        return playerId in itertools.chain(self.zerg.Ids, self.terran.Ids, self.PoolIds)

    @property
    def PoolIds(self):
      return [player.id for player in self.playerPool]