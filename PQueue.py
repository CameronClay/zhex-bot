import Region
from datetime import datetime, timezone

class QueueItm:
    def __init__(self, playerId):
        self.playerId = playerId
        self.addedAt = datetime.now(timezone.utc)

class PQueue:
    def __init__(self):
        self.queue = {reg:dict() for reg in Region.REGIONS}

    def __getitem__(self, key):
        return self.queue[key]

    def __iter__(self):
        return iter(self.queue.items())
    
    def add(self, region, playerId):
        self.queue[region][playerId] = datetime.now(timezone.utc)

    def remove_all(self, region, playerId):
        if region == Region.ALL:
            self.remove_all(Region.NA, playerId)
            self.remove_all(Region.EU, playerId)
        elif playerId in self.queue[region]:
            self.queue[region].pop(playerId)

    def remove(self, region, playerId):
        self.queue[region].remove(playerId)

    def clear(self, region):
        if region == Region.ALL:
            self.clear(Region.NA)
            self.clear(Region.EU)
        else:  
            self.queue[region].clear()

    def to_players(self, region, playerDB):
        return {playerDB.Find(id, region) for id,_ in self.queue[region].items()}
    
    @property
    def Ids(self):
        return iter(self.queue)
