
# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018
from util import PrimeGroup, ot_hash, xor_bytes

def ot_alice(self,socket, m0, m1):
    group = PrimeGroup()
    socket.send(group)
    socket.receive()

    c = group.rand_int()
    socket.send(c)
    socket.receive()
    h0 = socket.receive()
    socket.send('h0 received')

    h1 = group.mul(c, group.inv(h0))
    k = group.rand_int()
    c1 = group.gen_pow(k)

    e0 = xor_bytes(ot_hash(h0, len(m0)), str(m0).encode('UTF-8') )
    e1 = xor_bytes(ot_hash(h1, len(m1)), str(m1).encode('UTF-8') )

    socket.send((e0,e1,c1))
    socket.receive()

def ot_bob(self, socket, bit):
    group = socket.receive()
    socket.send('group received')

    c = socket.receive()
    socket.send('c received')
    x = group.rand_int()
    hb = group.gen_pow(x)
    socket.send(hb)
    socket.receive()
    (e0, e1, c1) = socket.receive()
    socket.send('e0, e1, c1 received')

    decrypt_hash = ot_hash(group.pow(c1,x))
    if bool(bit):
        return eval(xor_bytes(e1, decrypt_hash).decode('UTF-8'))
    else:
        return eval(xor_bytes(e0, decrypt_hash).decode('UTF-8'))






