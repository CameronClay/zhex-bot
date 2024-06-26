from src.Team import Team
from src.Player import Player, MatchRes, Race
from src.Region import Region

from enum import Enum
from copy import deepcopy
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

    def __init__(self, region: Region, playerPool: list[Player]):
        assert len(playerPool) == Game.N_PLAYERS

        self.id = IdGen()
        self.region = region
        self.state = State.TERRAN_PICK
        self.playerPool = {player.id:player for player in playerPool}
        self.zergCapt = self.ChooseCaptain(Race.ZERG)
        self.terranCapt = self.ChooseCaptain(Race.TERRAN)
        self.zerg = Team(self.zergCapt)
        self.terran = Team(self.terranCapt)
        self.playerTurn = self.terranCapt
        self.pickedCnt = 0
        self.timeStarted = None

    def ChooseCaptain(self, race: Race):
        oppRace = Race.Invert(race)
        players = filter(lambda p: p.racePref.race != oppRace, list(self.PoolPlayers))

        player = max(players, key=lambda player: player.elo[race])
        self.playerPool.pop(player.id)

        return player

    def Sub(self, pSubId: int, pSubWith: Player):
        #assert self.state != State.IN_GAME, "Cannot pick player while playing"
        if self.state == State.IN_GAME:
            if pSubId in self.zerg.Ids:
                self.zerg.Remove(pSubId)
                self.zerg.Add(pSubWith)
            elif pSubId in self.terran.Ids:
                self.terran.Remove(pSubId)
                self.terran.Add(pSubWith)
            else:
                raise AssertionError("Cannot sub player in illegal state")
        else:
            self.playerPool.pop(pSubId)
            self.playerPool[pSubWith.id] = pSubWith

    def __AddPlayer(self, player: Player):  
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

    def PickPlayer(self, playerId: int):
        assert self.state != State.IN_GAME, "Cannot pick player while playing"
        assert len(self.playerPool) != 0  , "Cannot pick player from empty pool"

        player = self.playerPool.get(playerId)
        assert player != None, "Cannot find player to pick"

        self.__AddPlayer(player)

        self.playerPool.pop(player.id)

        self.__PickLastPlayer()

    def ChangeTurn(self):   
        self.pickedCnt += 1
        if (self.pickedCnt == Game.TERRAN_PICK_CNT) and (self.state == State.TERRAN_PICK):
            self.state = State.ZERG_PICK
            self.playerTurn = self.zergCapt
        else:
            self.state = State.TERRAN_PICK
            self.playerTurn = self.terranCapt

    def CaptOnTeam(self, playerId: int):
        return self.zergCapt.id == playerId or self.terranCapt.id == playerId
    
    #get race of player
    def PlayerRace(self, playerId: int):
        if playerId in self.zerg.Ids:
            return "Zerg"
        elif playerId in self.terran.Ids:
            return "Terran"
        else:
            return ""

    def GetVictor(self, playerId: int, res: MatchRes):
        victor = ""
        if res == MatchRes.TIE:
            victor = "Tie"
        elif playerId in self.zerg.Ids and res == MatchRes.WIN:
            victor = "Zerg"
        else:
            victor = "Terran"
        return victor

    def MatchResult(self, captainId: int, res: MatchRes):
        notRes = MatchRes.TIE
        if res == MatchRes.WIN:
            notRes = MatchRes.LOSS
        elif res == MatchRes.LOSS:
            notRes = MatchRes.WIN

        if captainId == self.zergCapt.id:
            self.zerg.MatchResult(self.terran, Race.ZERG, res)
            self.terran.MatchResult(self.zerg, Race.TERRAN, notRes)
        elif captainId == self.terranCapt.id:
            self.zerg.MatchResult(self.terran, Race.ZERG, notRes)
            self.terran.MatchResult(self.zerg, Race.TERRAN, res)
        else:
            raise AssertionError(f"Must be a captain to report match")

    def PickAfk(self):
        filterPref = Race.ZERG if self.state == State.TERRAN_PICK else Race.TERRAN
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
    
    def IsPlaying(self, playerId: int):
        return playerId in self.AllPlayers

    @property
    def AllPlayers(self):
        return itertools.chain(self.zerg.Ids, self.terran.Ids, self.PoolIds)

    @property
    def PoolIds(self):
      return self.playerPool.keys()

    @property
    def PoolPlayers(self):
      return self.playerPool.values()

    def RunningDuration(self):
        return datetime.now() - self.timeStarted
