from Region import Region
from datetime import datetime

class PQueue:
    def __init__(self):
        self.queue = {reg:dict() for reg in Region.REGIONS}

    def __getitem__(self, key):
        return self.queue[key]

    def __iter__(self):
        return iter(self.queue.items())
    
    def add(self, region, playerId):
        self.queue[region][playerId] = datetime.now()

    #returns True if any where deleted
    def remove_all_of(self, region, playerId):
        if region == Region.ALL:
            return any([self.remove_all_of(reg, playerId) for reg in Region.REGIONS]) #list comprehension to ensure all are removed
        elif playerId in self.queue[region]:
            self.remove(region, playerId)
            return True
        return False

    def remove(self, region, playerId):
        self.queue[region].pop(playerId)

    def clear(self, region):
        if region == Region.ALL:
            for reg in Region.REGIONS:
                self.clear(reg)
        else:  
            self.queue[region].clear()

    def to_players(self, region, playerDB):
        return {playerDB.Find(id, region) for id,_ in self.queue[region].items()}
    
    def copy(self):
        return self.queue.copy()

    @property
    def ids(self):
        return iter(self.queue.items())

