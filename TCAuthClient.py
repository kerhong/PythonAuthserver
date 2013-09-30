import threading
from struct import unpack, pack
from TCAuthSettings import TCAuthSettings, Log, Debug
from TCBigNumber import TCBigNumber
import random
import hashlib
import time
from copy import deepcopy
from ATGoogleAuth import ATGoogleAuth

class TCAuthClient:
    def __init__(self, sock, address, server, dbpool):
        self.server = server
        self.sock = sock
        self.address = address
        self.authed = False
        self.locale = 0
        self.os = 0
        self.gamebuild = 0
        self.security = 0
        self.db = dbpool
        self.authenticator = None
        
        self.crypt_N = TCBigNumber()
        self.crypt_g = TCBigNumber()
        self.crypt_v = TCBigNumber()
        self.crypt_s = TCBigNumber()
        self.crypt_b = TCBigNumber()
        self.crypt_B = TCBigNumber()
        self.crypt_K = TCBigNumber()
        self.crypt_reconnectProof = TCBigNumber()
        
        self.crypt_N.SetHex('894B645E89E1535BBDAD5B8B290650530801B18EBFBF5E8FAB3C82872A3E9BB7')
        self.crypt_g.SetInt(7)
        
    def run(self):
        th = threading.Thread(target=self.handle)
        th.start()

    def recvall(self, size):
        msg = ''
        while len(msg) < size:
            part = self.sock.recv(size-len(msg))
            if part == '': 
                break
            msg += part
        return msg

    def handle(self):
        Log("Client connected [IP: {}]".format(self.address[0]))

        while True:            
            opcode = self.recvall(1)
            
            if len(opcode) != 1:
                break
            elif ord(opcode) == 0x00:
                if not self.handleAuthLogonChallenge():
                    break
            elif ord(opcode) == 0x01:
                if not self.handleAuthLogonProof():
                    break
            elif ord(opcode) == 0x02:
                if not self.handleReconnectChallenge():
                    break
            elif ord(opcode) == 0x03:
                if not self.handleReconnectProof():
                    break
            elif ord(opcode) == 0x10:
                if not self.handleRealmList():
                    break

        time.sleep(1) # Hack to be 'almost sure' that all data is delivered to client
        self.sock.close()
        Log("Client disconnected [IP: {}]".format(self.address[0]))

    def handleAuthLogonChallenge(self):
        Debug("->handleAuthLogonChallenge")
        
        result = 0
        
        header = self.sock.recv(3)
        if len(header) != 3:
            return False

        error, length = unpack('<BH', header)
        data = self.sock.recv(30)
        if len(data) != 30:
            return False

        gamename, version1, version2, version3, self.gamebuild, platform, self.os, self.country, timezone, ip, login_len = unpack('<IBBBHIIIIIB', data)
        
        self.login = self.sock.recv(login_len)
        if len(self.login) != login_len:
            return False
        
        Log("Account trying to log in [AccName: {}] [IP: {}]".format(self.login, self.address[0]))

        if TCAuthSettings.ALLOWED_BUILDS.count(self.gamebuild) == 0:
            result = 0x08
        else:            
            ban = self.db.QueryOne("""select bandate, unbandate from ip_banned where ip=%s union all select bandate, unbandate from account_banned b
                         join account a on a.id=b.id and a.username=%s and b.active=1 limit 1""", (self.address[0], self.login))
            if ban != None:
                if ban[0] == ban[1]:
                    result = 0x03 # Permanent ban
                else:
                    result = 0x0C # Temporary ban
            else:
                accinfo = self.db.QueryOne("""select acc.id, acc.sha_pass_hash, acc.v, acc.s, acc.locked, acc.last_ip, max(aca.gmlevel), aau.authentificator
                    from account acc left join account_access aca on acc.id=aca.id and aca.RealmID=-1 left join account_authentificator aau on acc.id=aau.account
                    where acc.username=%s""", (self.login,))    
                if accinfo == None or accinfo[0] == None:
                    result = 0x04 # Wrong username
                elif accinfo[4] != 0 and accinfo[5] != self.address[0]:
                    result = 0x0C # Account locked to different IP
                else:
                    db_v = accinfo[2]
                    db_s = accinfo[3]
                    
                    if db_v == None or db_s == None:
                        db_v = ''
                        db_s = ''

                    self.authenticator = accinfo[7]

                    self.security = accinfo[6]
                    if self.security == None:
                        self.security = 0
    
                    if len(db_v) != 64 or len(db_s) != 64:
                        self.RecalculateVS(accinfo[1])
                    else:
                        self.crypt_s.SetHex(db_s)
                        self.crypt_v.SetHex(db_v)
    
                    self.crypt_b.SetInt(random.randrange(0, 19 * 8))
                    gmod = self.crypt_g.ModExp(self.crypt_b.GetInt(), self.crypt_N.GetInt())
                    self.crypt_B.SetInt(((self.crypt_v.GetInt() * 3) + gmod.GetInt()) % self.crypt_N.GetInt())
                    
                    unk3 = TCBigNumber()
                    unk3.SetInt(random.randrange(0, 16 * 8))
    
                    response = pack('<BH', 0, 0)
                    response += self.crypt_B.GetBytes(32)
                    response += pack('<B', 1)
                    response += self.crypt_g.GetBytes(1)
                    response += pack('<B', 32)
                    response += self.crypt_N.GetBytes(32)
                    response += self.crypt_s.GetBytes(32)
                    response += unk3.GetBytes(16)
                    if self.authenticator:
                        response += pack('<BB', 4, 1)
                    else:
                        response += pack('<B', 0)
    
                    Log("Account passed LogonChallenge [AccName: {}] [IP: {}]".format(self.login, self.address[0]))
                    self.sock.sendall(response)
                    return True

        Log("Account failed LogonChallenge [AccName: {}] [IP: {}] [Error: {}]".format(self.login, self.address[0], result))
        self.sock.sendall(pack('<HB', 0, result))
        return False

    def handleAuthLogonProof(self):
        Debug("->handleAuthLogonProof")   

        tmp = self.sock.recv(32)
        if len(tmp) != 32: return False
        A = TCBigNumber()
        A.SetBytes(tmp)
        if A.GetInt() == 0: return False
        
        tmp = self.sock.recv(20)
        if len(tmp) != 20: return False
        m1 = TCBigNumber()
        m1.SetBytes(tmp)
        
        tmp = self.sock.recv(20)
        if len(tmp) != 20: return False
        crc = TCBigNumber()
        crc.SetBytes(tmp)
        
        if len(self.sock.recv(2)) != 2: return False

        sha = hashlib.sha1()
        sha.update(A.GetBytes())
        sha.update(self.crypt_B.GetBytes())
        
        u = TCBigNumber()
        u.SetBytes(sha.digest())

        S = TCBigNumber()
        S.SetInt(A.GetInt() * self.crypt_v.ModExp(u.GetInt(), self.crypt_N.GetInt()).GetInt())
        S = S.ModExp(self.crypt_b.GetInt(), self.crypt_N.GetInt())
        
        t = S.GetBytes(32)
        t1 = ''
        
        for i in range(16):
            t1 += t[i * 2]
        
        bytefix = TCBigNumber()    
        
        sha = hashlib.sha1()
        sha.update(t1)
        bytefix.SetBytes(sha.digest())
        t1 = bytefix.GetBytes(20)
        
        t2 = ''
        for i in range(16):
            t2 += t[i * 2 + 1]
            
        sha = hashlib.sha1()
        sha.update(t2)
        bytefix.SetBytes(sha.digest())
        t2 = bytefix.GetBytes(20)
        
        vK = ''
        for i in range(20):
            vK += t1[i]
            vK += t2[i]
        
        self.crypt_K.SetBytes(vK)
        
        sha = hashlib.sha1()
        sha.update(self.crypt_N.GetBytes())
        bytefix.SetBytes(sha.digest())
        tmp = bytefix.GetBytes(20)
        
        sha = hashlib.sha1()
        sha.update(self.crypt_g.GetBytes())
        bytefix.SetBytes(sha.digest())
        
        hsh = ''
        for i in range(20):
            h1 = int(tmp[i].encode('hex'), 16)
            h2 = int(bytefix.GetBytes(20)[i].encode('hex'), 16)
            hsh += chr(h1 ^ h2)
        
        t3 = TCBigNumber()
        t3.SetBytes(hsh)
                
        sha = hashlib.sha1()
        sha.update(self.login)
        
        t4 = TCBigNumber()
        t4.SetBytes(sha.digest())
        
        sha = hashlib.sha1()
        sha.update(t3.GetBytes(20))
        sha.update(t4.GetBytes(20))
        sha.update(self.crypt_s.GetBytes())
        sha.update(A.GetBytes())
        sha.update(self.crypt_B.GetBytes())
        sha.update(self.crypt_K.GetBytes())
        
        M = TCBigNumber()
        M.SetBytes(sha.digest())

        if M.GetInt() == m1.GetInt():
            if self.authenticator:
                passed = False
                tmp = self.sock.recv(1)
                if len(tmp) == 1:
                    tmp = unpack('<B', tmp)[0]
                    key = self.sock.recv(tmp)
                    if len(key) == tmp:
                        try:
                            key = int(key)
                            print key
                            if ATGoogleAuth(self.authenticator, key):
                                passed = True
                        except ValueError:
                            passed = False
                if not passed:
                    Log('Account failed LogonProof (otc) [AccName: {}] [IP: {}]'.format(self.login, self.address[0]))
                    self.sock.sendall(pack('<BBBB', 1, 4, 3, 0))
                    return False
                

            Log('Account passed LogonProof [AccName: {}] [IP: {}]'.format(self.login, self.address[0]))
            self.db.QueryOne("""UPDATE account SET sessionkey=%s, last_ip=%s, last_login=NOW(),
                         locale=%s, operatingSystem=%s WHERE username=%s""", (self.crypt_K.GetHex(),
                                                                              self.address[0],
                                                                              self.locale,
                                                                              self.os,
                                                                              self.login))
            sha = hashlib.sha1()
            sha.update(A.GetBytes())                      
            sha.update(M.GetBytes())
            sha.update(self.crypt_K.GetBytes())
            m2 = TCBigNumber()
            m2.SetBytes(sha.digest())
        
            response = pack('<BB', 1, 0)
            response += m2.GetBytes(20)
            response += pack('<IIH', 0x00800000, 0, 0)
            self.sock.sendall(response)
            
            self.authed = True
            return True
    
        Log('Account failed LogonProof [AccName: {}] [IP: {}]'.format(self.login, self.address[0]))
        self.sock.sendall(pack('<BBBB', 1, 4, 3, 0))
        return False

    def handleReconnectChallenge(self):
        Debug("->handleReconnectChallenge")

        header = self.sock.recv(3)
        if len(header) != 3:
            return False

        error, length = unpack('<BH', header)
        data = self.sock.recv(30)
        if len(data) != 30:
            return False

        gamename, version1, version2, version3, self.gamebuild, platform, self.os, self.country, timezone, ip, login_len = unpack('<IBBBHIIIIIB', data)
        
        self.login = self.sock.recv(login_len)
        if len(self.login) != login_len:
            return False

        accinfo = self.db.QueryOne("""select acc.id, acc.sessionkey, max(aca.gmlevel) from account acc left join account_access aca on acc.id=aca.id and aca.RealmID=-1
                     where acc.username=%s""", (self.login,))
        if accinfo == None or accinfo[0] == None:
            return False
        
        self.security = accinfo[2]
        if self.security == None:
            self.security = 0
        
        self.crypt_K.SetHex(accinfo[1])
        self.crypt_reconnectProof.SetRand(16)
        
        response = pack('<BB', 2, 0)
        response += self.crypt_reconnectProof.GetBytes(16)
        response += pack('<IIII', 0, 0, 0, 0)

        self.sock.sendall(response)
        return True

    def handleReconnectProof(self):
        Debug("->handleReconnectProof")

        t1 = TCBigNumber()
        R2 = TCBigNumber()

        tmp = self.sock.recv(16)
        if len(tmp) != 16: return False
        t1.SetBytes(tmp)
        
        tmp = self.sock.recv(20)
        if len(tmp) != 20: return False
        R2.SetBytes(tmp)
        
        if len(self.sock.recv(21)) != 21: return False
        
        sha = hashlib.sha1()
        sha.update(self.login)
        sha.update(t1.GetBytes())
        sha.update(self.crypt_reconnectProof.GetBytes())
        sha.update(self.crypt_K.GetBytes())
        
        res = TCBigNumber()
        res.SetBytes(sha.digest())
        
        if res.GetInt() == R2.GetInt():
            self.authed = True
            self.sock.sendall(pack('<BBH', 3, 0, 0))
            return True        

        return False

    def handleRealmList(self):
        Debug("->handleRealmList")
        if not self.authed: return False
        if len(self.sock.recv(4)) != 4: return False
        
        data = ''
        cnt = 0
        
        realms = deepcopy(self.server.realms)        
        
        for r in realms:
            if r['build'] != self.gamebuild: continue
            if r['security'] > self.security: continue
            
            data += pack('<BBB', r['icon'], 0, r['color'])
            data += r['name'] + chr(0) + r['address'] + chr(0)
            data += pack('<fBBB', r['population'], 0, r['timezone'], 0x2C)
            
            cnt = cnt + 1
        
        data += pack('<BB', 0x10, 0)
        
        res = pack('<BHIH', 16, 6 + len(data), 0, cnt)
        res += data
        self.sock.sendall(res)
        return True
        
    def RecalculateVS(self, pwhash):
        Debug("->RecalculateVS")
        
        self.crypt_s.SetRand(32)
        I = TCBigNumber()
        I.SetHex(pwhash)        
        sha = hashlib.sha1()
        sha.update(self.crypt_s.GetBytes())
        sha.update(I.GetBytes(20, True))        
        x = TCBigNumber()
        x.SetBytes(sha.digest())        
        self.crypt_v = self.crypt_g.ModExp(x.GetInt(), self.crypt_N.GetInt())
        self.db.QueryOne("""UPDATE account SET v=%s, s=%s WHERE username=%s""", (self.crypt_v.GetHex(),
                                                                          self.crypt_s.GetHex(),
                                                                          self.login))
