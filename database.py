import datetime
import sqlite3

import config as cfg


class Database():
    __instance = None

    @staticmethod
    def get_instance():
        if Database.__instance is None:
            print("Create Database Instance")
            Database.__instance = Database()
        return Database.__instance

    def __init__(self) -> None:
        if Database.__instance is not None:
            raise Exception(
                "Use the get_instance() method to " +
                "get an instance of the Database"
            )

        self.conn = sqlite3.connect(
            "database/yams.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id            INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
                gameId        VARCHAR UNIQUE NOT NULL,
                createdAt     DATETIME NOT NULL,
                [1]           INTEGER,
                [2]           INTEGER,
                [3]           INTEGER,
                [4]           INTEGER,
                [5]           INTEGER,
                [6]           INTEGER,
                brelan        INTEGER,
                [full]        INTEGER,
                carre         INTEGER,
                yams          INTEGER,
                smallSequence INTEGER,
                largeSequence INTEGER,
                chance        INTEGER
                );
        ''')

    def setGameId(self, gameId):
        self.cursor.execute(
            '''INSERT INTO scores (gameId, createdAt) VALUES (?, ?)''',
            (gameId, datetime.datetime.now(),))
        self.conn.commit()

    def updateScore(self, gameId, name, score):
        self.cursor.execute(
            "UPDATE scores SET '%s' = ? WHERE `gameId` = ?" % (name),
            [score, gameId])
        self.conn.commit()

    def getAllScores(self):
        combinationsKeys = ' + '.join(["IFNULL(`%s`, 0)" % (i)
                                      for i in list(
                                          cfg.combinationsList.keys()
        )])
        self.cursor.execute(
            """SELECT gameId, createdAt, (%s) AS scoreSum FROM scores""" %
            (combinationsKeys))
        records = self.cursor.fetchall()
        return [dict(r) for r in records]

    def getDBScore(self, gameId):
        combinationsKeys = ', '.join(
            ["`%s`" % (i) for i in list(cfg.combinationsList.keys())])
        self.cursor.execute("""SELECT %s FROM scores WHERE `gameId` = ?""" % (
            combinationsKeys), [gameId, ])
        records = self.cursor.fetchall()

        for r in records:
            return (dict(r))
