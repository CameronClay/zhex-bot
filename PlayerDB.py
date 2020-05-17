import sqlite3
from Player import Player
import Region

class PlayerDB:
    DATABASE_NAME = 'players.db'
    def __init__(self):
        self.conn = sqlite3.connect(PlayerDB.DATABASE_NAME)
        cur = self.conn.cursor()
        cur.execute('''create table if not exists players (
                    id         integer,
                    region     text,
                    wins       integer, 
                    loses      integer,
                    games      integer,
                    elo        real,
                    lastPlayed text,
                    primary key (id, region)
                    unique(id, region)
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
        self.conn.execute('''insert or ignore into players (id, region, wins, loses, games, elo, lastPlayed)
                    values (?, ?, ?, ?, ?, ?, ?)''', (player.id, player.region, player.wins, player.loses, player.games, player.elo, player.lastPlayed))
        self.conn.commit()

    def UnRegister(self, playerId, region):
        if region == Region.ALL:
            self.conn.execute(f'''delete from players where id = ?''', (playerId))
        else:
            self.conn.execute(f'''delete from players where id = ? and region = ?''', (playerId, region))
        self.conn.commit()

    def UpdateStats(self, player):
        sql = f'''update players
            set
                wins = ?, 
                loses = ?, 
                games = ?,
                elo = ?, 
                lastPlayed = ?
            where id = ? and region = ?'''

        self.conn.execute(sql, (player.wins, player.loses, player.games, player.elo, player.lastPlayed, player.id, player.region))
        self.conn.commit()
        
    def Close(self):
        self.conn.close()