import sqlite3
from Player import Player

class PlayerDB:
    DATABASE_NAME = 'players.db'
    def __init__(self):
        self.conn = sqlite3.connect(PlayerDB.DATABASE_NAME)
        cur = self.conn.cursor()
        cur.execute('''create table if not exists players                  
                    (id        text     primary key,
                    wins       INTEGER, 
                    loses      INTEGER,
                    elo        REAL,
                    lastPlayed text);''')

    def IsRegistered(self, playerId):
        return self.Find(playerId) != None

    def Find(self, playerId):
        res = self.conn.execute(f'''select * from players where id = {playerId}''')
        return res.fetchone()

    def Register(self, player):
        self.conn.execute('''insert into players (id, wins, loses, elo, lastPlayed)
                    values (?, ?, ?, ?, ?)''', (player.id, player.wins, player.loses, player.elo, player.lastPlayed))
        self.conn.commit()

    def UnRegister(self, playerId):
        self.conn.execute(f'''delete from players where id = {playerId}''')
        self.conn.commit()

    def UpdateStats(self, player):
        self.conn.execute(f'''update players (id, wins, loses, elo, lastPlayed) 
            set wins = {player.wins}, loses = {player.loses}, elo = {player.elo}
            where id = {player.id}, lastPlayed = {player.lastPlayed}''')
        self.conn.commit()
        
    def Close(self):
        self.conn.close()

        
    