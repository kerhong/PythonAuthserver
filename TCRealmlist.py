import threading
from TCAuthSettings import TCAuthSettings, Log, Debug
import MySQLdb
import time

class TCRealmlist:
    def run(self, server):
        self.server = server
        th = threading.Thread(target=self.handle)
        th.start()
        
    def handle(self):
        Debug("Realmlist thread started")

        self.db = MySQLdb.connect(host=TCAuthSettings.DB_HOST,
                                 user=TCAuthSettings.DB_USER,
                                 passwd=TCAuthSettings.DB_PASSWORD,
                                 db=TCAuthSettings.DB_DATABASE)
        
        while True:
            c = self.db.cursor()
            c.execute("""DELETE FROM ip_banned WHERE unbandate<>bandate AND unbandate<=UNIX_TIMESTAMP()""")
            c.execute("""UPDATE account_banned SET active = 0 WHERE active = 1 AND unbandate<>bandate AND unbandate<=UNIX_TIMESTAMP()""")
            c.execute("""select id, name, address, port, icon, color, timezone, allowedsecuritylevel, population, gamebuild from realmlist""")

            res = c.fetchall()
            tmp = []            
            for r in res:
                tmp.append({
                            'id': int(r[0]),
                            'name': r[1],
                            'address': r[2] + ':' + str(r[3]),
                            'icon': int(r[4]),
                            'color': int(r[5]),
                            'timezone': int(r[6]),
                            'security': int(r[7]),
                            'population': r[8],
                            'build': int(r[9])
                           })
            self.server.realms = tmp

            time.sleep(TCAuthSettings.REALMLIST_UPDATE_DELAY)

        Debug("Realmlist thread quit")
