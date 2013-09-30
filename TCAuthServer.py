import socket
from TCAuthClient import TCAuthClient
from TCAuthSettings import TCAuthSettings
from TCRealmlist import TCRealmlist
from TCDBPool import TCDBPool

class TCAuthServer:
    def run(self):
        self.db = TCDBPool()
        self.db.Connect(TCAuthSettings.DB_HOST, TCAuthSettings.DB_USER, TCAuthSettings.DB_PASSWORD, TCAuthSettings.DB_DATABASE, TCAuthSettings.DB_CONNECTIONS)

        self.realmlist = TCRealmlist()
        self.realmlist.run(self, self.db)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((TCAuthSettings.LISTEN_IP, TCAuthSettings.LISTEN_PORT))
        sock.listen(TCAuthSettings.LISTEN_BACKLOG)
        
        while True:
            (csock, address) = sock.accept()
            client = TCAuthClient(csock, address, self, self.db)
            client.run()
