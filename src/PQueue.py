from src.Region import Region
from src.Game import Game
from src.PlayerDB import PlayerDB

from datetime import datetime

class PQueue:
    def __init__(self):
        self.queue = {reg:dict() for reg in Region.REGIONS}

    def __getitem__(self, key: Region):
        return self.queue[key]
    
    def __iter__(self):
        return iter(self.queue.items())
    
    def remove_slice(self, region: Region, start: int, stop: int):
        items = list(self.queue[region].items())[start:stop]
        for id, _ in items:
            self.remove(region, id)
        return items

    def set_queue(self, region: Region, items: dict):
        self.clear(region)
        self.queue[region].update(items)
    
    def add(self, region: Region, playerId: int):
        self.queue[region][playerId] = datetime.now()

    #returns True if any where deleted
    def remove_all_of(self, region: Region, playerId: int):
        if region == Region.ALL:
            return any([self.remove_all_of(reg, playerId) for reg in Region.REGIONS]) #list comprehension to ensure all are removed
        elif playerId in self.queue[region]:
            self.remove(region, playerId)
            return True
        return False

    def remove(self, region: Region, playerId: int):
        self.queue[region].pop(playerId)

    def clear(self, region: Region):
        for reg in Region(region).ToList():
            self.queue[reg].clear()

    def return_players(self, region: Region, playerDB: PlayerDB):
        retQueue = self.remove_slice(region, 0, Game.N_PLAYERS)
        return {playerDB.Find(id, region) for id,_ in retQueue}
    
    def copy(self):
        return self.queue.copy()

    def is_full(self, reg: Region):
        assert reg != Region.ALL
        return len(self.queue[reg]) >= Game.N_PLAYERS

    @property
    def ids(self):
        return iter(self.queue.items())

