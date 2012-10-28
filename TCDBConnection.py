import MySQLdb

class TCDBConnection:
    MAX_ERROR_RETRIES = 5
    
    def __init__(self):
        self.db = None
    
    # Returns true if error handled and operation can be retried
    def HandleError(self, e):
        if e == 2006 or e == 2003:
            return self.Connect(self.host, self.user, self.password, self.database)
        print "Unhandled MySQL error: {}".format(e)
        return False
    
    def Disconnect(self):
        self.db = None
    
    def Connect(self, _host, _user, _password, _database, retry = 0):
        self.host = _host
        self.user = _user
        self.password = _password
        self.database = _database
        try:
            self.db = MySQLdb.connect(host=_host, user=_user, passwd=_password, db=_database)
        except MySQLdb.OperationalError as e:
            if retry > self.MAX_ERROR_RETRIES:
                print "TCDBConnection:Connect failed: Retry count exceeded (MySQL error {})".format(e[0])
                return False
            elif self.HandleError(e[0]):
                return self.Connect(_host, _user, _password, _database, retry + 1)
            else:
                print "TCDBConnection:Connect failed: Error not handled (MySQL error {})".format(e[0])
                return False
        self.db.autocommit(True)
        return True
    
    def QueryOne(self, query, args = None, retry = 0):
        if self.db == None:
            return None
        try:
            c = self.db.cursor()
            c.execute(query, args)
        except MySQLdb.OperationalError as e:
            if retry > self.MAX_ERROR_RETRIES:
                print "TCDBConnection:QueryOne failed: Retry count exceeded (MySQL error {})".format(e[0])
            elif self.HandleError(e[0]):
                return self.QueryOne(query, args, retry)
            else:
                print "TCDBConnection:QueryOne failed: Error not handled (MySQL error {})".format(e[0])
                return None
        return c.fetchone()
    
    def QueryAll(self, query, args = None, retry = 0):
        if self.db == None:
            return None
        try:
            c = self.db.cursor()
            c.execute(query, args)
        except MySQLdb.OperationalError as e:
            if retry > self.MAX_ERROR_RETRIES:
                print "TCDBConnection:QueryAll failed: Retry count exceeded (MySQL error {})".format(e[0])
            elif self.HandleError(e[0]):
                return self.QueryAll(query, args, retry)
            else:
                print "TCDBConnection:QueryAll failed: Error not handled (MySQL error {})".format(e[0])
                return None
        return c.fetchall()
