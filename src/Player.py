from enum import IntEnum
from datetime import datetime
import time
import discord
from discord.ext import commands

from src.Region import Region

class MatchRes(IntEnum):
    WIN = 1,
    LOSS = 0,
    TIE = 2

class Race:
    ZERG = "Z"
    TERRAN = "T"
    ANY = "A"    
    RACES = [ZERG, TERRAN]
    VALID_RACES = [ZERG, TERRAN, ANY]

    def __init__(self, race: str):
        self.race = race

    @classmethod
    async def convert(cls, ctx, argument):
        if not argument.upper() in Race.VALID_RACES:
            raise commands.ArgumentParsingError(f"Invalid race; expected {'/'.join(Race.VALID_RACES)}")
        
        return cls(argument)

    def Valid(self):
         return self.race in Race.VALID_RACES

    #return opposite race (T->Z, Z->T)
    @staticmethod
    def Invert(race: str):
        return Race.ZERG if race == Race.TERRAN else Race.TERRAN
        
    def ToList(self):
        if self.Valid():
            return Race.RACES if self.race == Race.ANY else [self.race]
        return []

class Player:
    AMOUNT = 50
    def __init__(self, id: int, region: Region, zwins = 0, zloses = 0, zties = 0, zelo = 1500, twins = 0, tloses = 0, tties = 0, telo = 1500, lastPlayed = None, racePref = Race.ANY):
        self.id = id
        self.region = region

        self.wins = {Race.ZERG : zwins, Race.TERRAN : twins}
        self.loses = {Race.ZERG : zloses, Race.TERRAN : tloses}
        self.ties = {Race.ZERG : zties, Race.TERRAN : tties}
        self.elo = {Race.ZERG : zelo, Race.TERRAN : telo}

        self.lastPlayed = lastPlayed
        self.racePref = Race(racePref) #because of db conversion to text

    def Ratio(self, race: Race):
        return self.wins[race] / (self.wins[race] + self.loses[race])

    @property 
    def zwins(self):
        return self.wins[Race.ZERG]
    @property 
    def zloses(self):
        return self.loses[Race.ZERG]
    @property 
    def zties(self):
        return self.ties[Race.ZERG]
    @property 
    def zelo(self):
        return self.elo[Race.ZERG]

    @property 
    def twins(self):
        return self.wins[Race.TERRAN]
    @property 
    def tloses(self):
        return self.loses[Race.TERRAN]
    @property 
    def tties(self):
        return self.ties[Race.TERRAN]
    @property 
    def telo(self):
        return self.elo[Race.TERRAN]
    
    @property
    def zratio(self):
        return self.Ratio(Race.ZERG)
    @property
    def tratio(self):
        return self.Ratio(Race.TERRAN)

    def Games(self, race: Race):
        return self.wins[race] + self.loses[race] + self.ties[race]

    def SetPlayed(self):
        self.lastPlayed = datetime.utcnow().strftime("%m/%d/%Y %H:%M")

    def MatchResult(self, ea: float, race: Race, res: MatchRes):
        assert race != Race.ANY

        k = 25 if self.Games(race) < 30 else 15
        if res != MatchRes.TIE:
            self.elo[race] = max(self.elo[race] + k * (int(res) - ea), 0)

        if res == MatchRes.WIN:
            self.wins[race] += 1
        elif res == MatchRes.LOSS:
            self.loses[race] += 1
        elif res == MatchRes.TIE:
            self.ties[race] += 1

        self.SetPlayed()