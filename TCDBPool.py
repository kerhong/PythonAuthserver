from TCDBConnection import TCDBConnection
from Queue import Queue

class TCDBPool:
    def __init__(self):
        self.connections = {}
        self.free = Queue()
        self.cons = 0
    
    def Connect(self, _host, _user, _password, _database, _connections):
        self.cons = _connections
        for i in range(_connections):
            con = TCDBConnection()
            con.Connect(_host, _user, _password, _database)
            self.connections[i] = con
            self.free.put(i)
    
    def GetConnection(self):
        i = self.free.get()
        return (i, self.connections[i])
    
    def FreeConnection(self, i):
        self.free.put(i)
    
    def QueryOne(self, query, args = None):
        i = -1
        try:
            i, con = self.GetConnection()
            return con.QueryOne(query, args)
        finally:
            if i != -1:
                self.FreeConnection(i)
                
    def QueryAll(self, query, args = None):
        i = -1
        try:
            i, con = self.GetConnection()
            return con.QueryAll(query, args)
        finally:
            if i != -1:
                self.FreeConnection(i)
