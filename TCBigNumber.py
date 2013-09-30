import random

class TCBigNumber:
    def __init__(self):
        self.val = 0
        self.len = 0

    def SetInt(self, i):
        self.val = i
        self.len = 0

    def SetHex(self, i):
        self.val = int(self.StripHex(i), 16)
        if len(i) % 2:
            self.len = (len(i) + 1) / 2
        else:
            self.len = len(i) / 2

    def SetBytes(self, i):
        h1 = i.encode('hex')
        h2 = ''
        while len(h1):
            h2 += h1[-2:]
            h1 = h1[:-2]
        self.SetHex(h2)
        self.len = len(i)

    def SetRand(self, l):
        self.SetHex(''.join(chr(random.randrange(0, 255)) for _ in range(l)).encode('hex'))

    def StripHex(self, h):
        h = h.lower()
        if h.endswith('l'):
            h = h[:-1]
        if h.startswith('0x'):
            h = h[2:]
        return h

    def GetLen(self):
        return self.len

    def GetHex(self):
        res = self.StripHex(hex(self.val))
        if len(res) % 2:
            res = '0' + res
        while len(res) < self.len * 2:
            res = '00' + res
        return res

    def GetInt(self):
        return self.val

    def GetBytes(self, l = 0, rev = False):
        ret = self.GetHex()
        if l:
            while len(ret) < l * 2:
                ret = ret + '00'
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
