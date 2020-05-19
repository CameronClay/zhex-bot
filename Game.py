from Team import Team
from enum import Enum
from copy import deepcopy
from Player import MatchRes, RacePref
import itertools
from datetime import datetime, timezone
from random import randint

class State(Enum):
    ZERG_PICK = 0,
    TERRAN_PICK = 1,
    IN_GAME = 2

def IdGen():
    id = 0
    def wrapper():
        return id + 1

    return wrapper

class Game:
    SIZE_ZERG = 2
    SIZE_TERRAN = 6
    N_PLAYERS = 8
    
    TERRAN_PICK_CNT = 2
    ZERG_PICK_CNT = 1

    def __init__(self, region, playerPool):
        assert len(playerPool) == Game.N_PLAYERS

        self.id = IdGen()
        self.region = region
        self.state = State.TERRAN_PICK
        self.playerPool = {player.id:player for player in playerPool}
        self.zergCapt = self.ChooseCaptain(State.ZERG_PICK)
        self.terranCapt = self.ChooseCaptain(State.TERRAN_PICK)
        self.zerg = Team(self.zergCapt)
        self.terran = Team(self.terranCapt)
        self.playerTurn = self.terranCapt
        self.pickedCnt = 0
        self.timeStarted = None

    def ChooseCaptain(self, team : State):
        filterPref = RacePref.ZERG if team == State.TERRAN_PICK else RacePref.TERRAN
        players = filter(lambda p: p.racePref != filterPref, list(self.PoolPlayers))

        player = max(players, key=lambda player: player.elo)
        self.playerPool.pop(player.id)

        return player

    def Sub(self, pSubId, pSubWith):
        assert self.state != State.IN_GAME, "Cannot pick player while playing"
        self.playerPool.remove(pSubId)
        self.playerPool[pSubWith.id] = pSubWith

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
        self.timeStarted = datetime.now()

    def PickPlayer(self, playerId):
        assert self.state != State.IN_GAME, "Cannot pick player while playing"
        assert len(self.playerPool) != 0  , "Cannot pick player from empty pool"

        player = self.playerPool.get(playerId)
        assert player != None, "Cannot find player to pick"

        self.__AddPlayer(player)

        self.playerPool.remove(player)

        self.__PickLastPlayer()

    def ChangeTurn(self):   
        self.pickedCnt += 1
        if (self.pickedCnt == Game.TERRAN_PICK_CNT) and (self.state == State.TERRAN_PICK):
            self.state = State.ZERG_PICK
            self.playerTurn = self.zergCapt
        else:
            self.state = State.TERRAN_PICK
            self.playerTurn = self.terranCapt

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
        notRes = MatchRes.TIE
        if res == MatchRes.WIN:
            notRes = MatchRes.LOSS
        elif res == MatchRes.LOSS:
            notRes = MatchRes.WIN

        if captainId == self.zergCapt.id:
            self.zerg.MatchResult(self.terran, res)
            self.terran.MatchResult(self.zerg, notRes)
        elif captainId == self.terranCapt.id:
            self.zerg.MatchResult(self.terran, notRes)
            self.terran.MatchResult(self.zerg, res)
        else:
            raise AssertionError(f"Must be a captain to report match")

    def PickAfk(self):
        filterPref = RacePref.ZERG if self.state == State.TERRAN_PICK else RacePref.TERRAN
        players = list(filter(lambda p: p.racePref != filterPref, list(self.PoolPlayers)))
        pickedPlayer = None
        if len(players) == 0:
            _,pickedPlayer = self.playerPool.popitem()
        else:
            pickedPlayer = players[randint(0, len(players) - 1)]
            self.playerPool.pop(pickedPlayer.id)

        self.__AddPlayer(pickedPlayer)
        self.__PickLastPlayer()
        return pickedPlayer
    
    def IsPlaying(self, playerId):
        return playerId in itertools.chain(self.zerg.Ids, self.terran.Ids, self.PoolIds)

    @property
    def PoolIds(self):
      return self.playerPool.keys()

    @property
    def PoolPlayers(self):
      return self.playerPool.values()

    def RunningDuration(self):
        return datetime.now() - self.timeStarted
