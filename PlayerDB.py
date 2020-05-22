import psycopg2
from Player import Player
from Region import Region

from configparser import ConfigParser

class PlayerDB:
    @staticmethod
    def config(filename='database.ini', section='postgresql'):
        # create a parser
        parser = ConfigParser()
        # read config file
        parser.read(filename)

        # get section, default to postgresql
        if parser.has_section(section):
            return {param[0]:param[1] for param in parser.items(section)}
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    def __init__(self):
        params = PlayerDB.config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')

        self.conn = psycopg2.connect(**params)
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

    def IsRegistered(self, playerId, region : Region):
        if region == Region.ALL:
            return all(self.IsRegistered(playerId, region) for region in Region.REGIONS)
        else:
            res = self.conn.execute(f'''select * from players where id = %s and region = %s''', (playerId, region))
            res = res.fetchone()
            return res != None
            
    # region must not be all
    def Find(self, playerId, region : Region):
        res = self.conn.execute(f'''select * from players where id = %s and region = %s''', (playerId, region))
        res = res.fetchone()
        if res:
            return Player(*res)
        return None

    def Register(self, player):
        self.conn.execute('''insert or ignore into players (id, region, zwins, zloses, zties, zelo, twins, tloses, tties, telo, lastPlayed, racePref)
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', (player.id, player.region, player.zwins, player.zloses, player.zties, player.zelo,
                    player.twins, player.tloses, player.tties, player.telo, 
                    player.lastPlayed, player.racePref.race))
        self.conn.commit()

    def UnRegister(self, playerId, region : Region):
        if region == Region.ALL:
            self.conn.execute(f'''delete from players where id = %s''', (playerId, ))
        else:
            self.conn.execute(f'''delete from players where id = %s and region = %s''', (playerId, region))
        self.conn.commit()

    def UpdatePlayer(self, player):
        sql = f'''update players
            set
                zwins = %s, 
                zloses = %s, 
                zties = %s,
                zelo = %s, 
                twins = %s, 
                tloses = %s, 
                tties = %s,
                telo = %s, 
                lastPlayed = %s,
                racePref = %s
            where id = %s and region = %s'''

        self.conn.execute(sql, (player.zwins, player.zloses, player.zties, player.zelo, player.twins, player.tloses, player.tties, player.telo,
            player.lastPlayed, player.racePref.race, player.id, player.region))
        self.conn.commit()
        
    def Close(self):
        self.conn.close()