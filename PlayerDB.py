import sqlite3
from Player import Player

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
                    );''')

    def IsRegistered(self, playerId):
        res = self.conn.execute(f'''select * from players where id = ?''', (playerId, ))
        res = res.fetchone()
        return res

    def Find(self, playerId, region):
        res = self.conn.execute(f'''select * from players where id = ? and region = ?''', (playerId, region))
        res = res.fetchone()
        if res:
            return Player(*res)
        return None

    def Register(self, player):
        self.conn.execute('''insert into players (id, region, wins, loses, games, elo, lastPlayed)
                    values (?, ?, ?, ?, ?, ?, ?)''', (player.id, player.region, player.wins, player.loses, player.games, player.elo, player.lastPlayed))
        self.conn.commit()

    def UnRegister(self, playerId):
        self.conn.execute(f'''delete from players where id = {playerId}''')
        self.conn.commit()

    def UpdateStats(self, player):
        #self.conn.execute(
        #'''update players
        #   set 
        #       wins = {player.wins}, 
        #       loses = {player.loses}, 
        #       elo = {player.elo}, 
        #       lastPlayed = {player.lastPlayed}
        #   where id = {player.id}''')

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