import random

class TCBigNumber:
    def __init__(self):
        self.n = 0
        
    def SetInt(self, i):
        self.n = i
        
    def SetHex(self, i):
        self.n = int(self.StripHex(i), 16)
    
    def SetBytes(self, i):        
        self.SetHex(i.encode('hex'))
        h1 = self.GetHex()
        h2 = ''
        while len(h1):
            h2 += h1[-2:]
            h1 = h1[:-2]
        self.SetHex(h2)
    
    def SetRand(self, l):
        self.SetHex(''.join(chr(random.randrange(0, 255)) for i in range(l)).encode('hex'))
    
    def StripHex(self, h):
        h = h.lower()
        if h.endswith('l'):
            h = h[:-1]
        if h.startswith('0x'):
            h = h[2:]
        return h
        
    
    def GetHex(self):
        res = self.StripHex(hex(self.n))
        if len(res) % 2:
            res = '0' + res
        return res
    
    def GetInt(self):
        return self.n
    
    def GetBytes(self, l = 0, rev = False):
        ret = self.GetHex()
        if l:
            while len(ret) < l * 2:
                ret = '00' + ret
        res = []
        for i in range(0, len(ret), 2):
            res.append(chr(int(ret[i:i+2], 16)))
        
        if not rev:
            res.reverse()
            
        return ''.join(res)

    def ModExp(self, u, n):
        s = 1
        t = self.GetInt()
        while u:
            if u & 1:
                s = (s * t) % n
            u >>= 1
            t = (t * t) % n
        
        res = TCBigNumber()
        res.SetInt(s)
        return res
        