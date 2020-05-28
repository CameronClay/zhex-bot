import psycopg2
from Player import Player
from Region import Region

from configparser import ConfigParser
import re
import os

class PlayerDB:
    @staticmethod
    def Config(filename='database.ini', section='postgresql'):
        parser = ConfigParser()
        parser.read(filename)

        if parser.has_section(section):
            return {param[0]:param[1] for param in parser.items(section)}
        else:
            raise Exception(f'Section {section} not found in the {filename} file')

    @staticmethod
    def ParseURL(url : str):
        #user:password@host:port/dbname
        pRe = re.compile('postgres://(.*):(.*)@(.*):(.*)/(.*)')
        m = pRe.match(url)
        return {'user':m.group(0), 'password':m.group(1), 'host':m.group(2), 'port':m.group(3), 'dbname':m.group(4)}


    def __init__(self):
        self.__Initialize()

    def __Initialize(self):
        DATABASE_URL = os.environ['DATABASE_URL']
        params = PlayerDB.ParseURL(DATABASE_URL)
        #params = PlayerDB.Config()

        print('Connecting to the PostgreSQL database...')

        self.conn = psycopg2.connect(**params)
        self.cur = self.conn.cursor()
        self.cur.execute('''create table if not exists players (
                    id         bigint,
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
                    primary key (id, region),
                    unique (id, region)
                    );''')

    def IsRegistered(self, playerId, region : Region):
        if region == Region.ALL:
            return all(self.IsRegistered(playerId, region) for region in Region.REGIONS)
        else:
            self.cur.execute(f'''select id from players where id = %s and region = %s''', (playerId, region))
            return self.cur.fetchone() != None

    # region must not be all
    def Find(self, playerId, region : Region):
        assert region != Region.ALL

        self.cur.execute(f'''select * from players where id = %s and region = %s''', (playerId, region))
        res = self.cur.fetchone()
        if res:
            return Player(*res)
        return None

    def Register(self, player):
        self.cur.execute('''insert into players (id, region, zwins, zloses, zties, zelo, twins, tloses, tties, telo, lastPlayed, racePref)
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', (player.id, player.region, player.zwins, player.zloses, player.zties, player.zelo,
                    player.twins, player.tloses, player.tties, player.telo, 
                    player.lastPlayed, player.racePref.race))
        self.conn.commit()

    def UnRegister(self, playerId, region : Region):
        if region == Region.ALL:
            self.cur.execute(f'''delete from players where id = %s''', (playerId, ))
        else:
            self.conn.execute(f'''delete from players where id = %s and region = %s''', (playerId, region))
        self.conn.commit()

    def UpdateStats(self, player):
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

        self.cur.execute(sql, (player.zwins, player.zloses, player.zties, player.zelo, player.twins, player.tloses, player.tties, player.telo,
            player.lastPlayed, player.racePref.race, player.id, player.region))
        self.conn.commit()

    def Recreate(self):
        self.cur.execute('''drop table if exists players''')
        self.Close()
        self.__Initialize()
        
    def Close(self):
        self.conn.close()