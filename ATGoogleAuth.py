import hmac, base64, struct, hashlib, time

def get_hotp_token(secret, intervals_no):
    key = base64.b32decode(secret, True)
    msg = struct.pack(">Q", intervals_no)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = ord(h[19]) & 15
    h = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
    return h

def ATGoogleAuth(secret, password):
    tick = int(time.time()) / 30
    for i in range(-1, 2):
        if get_hotp_token(secret, tick + i) == password:
            return True
    return False
