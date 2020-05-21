import sqlite3
from Player import Player
from Region import Region

class PlayerDB:
    DATABASE_NAME = 'players.db'
    def __init__(self):
        self.conn = sqlite3.connect(PlayerDB.DATABASE_NAME)
        cur = self.conn.cursor()
        cur.execute('''create table if not exists players (
                    id         integer,
                    region     text,
                    zwins      integer, 
                    zloses     integer,
                    zties      integer,
                    zelo       real,
                    twins      integer, 
                    tloses     integer,
                    tties      integer,
                    telo       real,
                    lastPlayed text,
                    racePref   text,
                    primary key (id, region)
                    unique (id, region)
                    );''')

    def IsRegistered(self, playerId, region):
        if region == Region.ALL:
            return all(self.IsRegistered(playerId, region) for region in Region.REGIONS)
        else:
            res = self.conn.execute(f'''select * from players where id = ? and region = ?''', (playerId, region))
            res = res.fetchone()
            return res != None
    # region must not be all
    def Find(self, playerId, region):
        res = self.conn.execute(f'''select * from players where id = ? and region = ?''', (playerId, region))
        res = res.fetchone()
        if res:
            return Player(*res)
        return None

    def Register(self, player):
        self.conn.execute('''insert or ignore into players (id, region, zwins, zloses, zties, zelo, twins, tloses, tties, telo, lastPlayed, racePref)
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (player.id, player.region, player.zwins, player.zloses, player.zties, player.zelo,
                    player.twins, player.tloses, player.tties, player.telo, 
                    player.lastPlayed, player.racePref.race))
        self.conn.commit()

    def UnRegister(self, playerId, region):
        if region == Region.ALL:
            self.conn.execute(f'''delete from players where id = ?''', (playerId, ))
        else:
            self.conn.execute(f'''delete from players where id = ? and region = ?''', (playerId, region))
        self.conn.commit()

    def UpdateStats(self, player):
        sql = f'''update players
            set
                zwins = ?, 
                zloses = ?, 
                zties = ?,
                zelo = ?, 
                twins = ?, 
                tloses = ?, 
                tties = ?,
                telo = ?, 
                lastPlayed = ?,
                racePref = ?
            where id = ? and region = ?'''

        self.conn.execute(sql, (player.zwins, player.zloses, player.zties, player.zelo, player.twins, player.tloses, player.tties, player.telo,
            player.lastPlayed, player.racePref.race, player.id, player.region))
        self.conn.commit()
        
    def Close(self):
        self.conn.close()