import socket
from TCAuthClient import TCAuthClient
from TCAuthSettings import TCAuthSettings
from TCRealmlist import TCRealmlist

class TCAuthServer:
    def run(self):
        self.realmlist = TCRealmlist()
        self.realmlist.run(self)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((TCAuthSettings.LISTEN_IP, TCAuthSettings.LISTEN_PORT))
        sock.listen(TCAuthSettings.LISTEN_BACKLOG)
        
        while True:
            (csock, address) = sock.accept()
            client = TCAuthClient(csock, address, self)
            client.run()
