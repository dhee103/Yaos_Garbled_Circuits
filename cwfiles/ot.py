# yao garbled circuit evaluation v1. simple version based on smart
# naranker dulay, dept of computing, imperial college, october 2018
from util import PrimeGroup, ot_hash, xor_bytes


# implemnetation of algorithm from Section 20.3
def ot_alice(socket, m0, m1):
    group = PrimeGroup()
    socket.send(group)
    socket.receive()

    c = group.rand_int()
    socket.send(c)
    socket.receive()
    socket.send('ok')
    h0 = socket.receive()
    socket.send('h0 received')
    socket.receive()

    h1 = group.mul(c, group.inv(h0))
    k = group.rand_int()
    c1 = group.gen_pow(k)

    # tuple encoded as string
    bm0 = str(m0).encode('UTF-8')
    bm1 = str(m1).encode('UTF-8')

    e0 = xor_bytes(ot_hash(group.pow(h0, k), len(bm0)), bm0)
    e1 = xor_bytes(ot_hash(group.pow(h1, k), len(bm1)), bm1)

    socket.send((e0, e1, c1, len(bm0)))
    socket.receive()


def ot_bob(socket, bit):
    group = socket.receive()
    socket.send('group received')

    c = socket.receive()
    socket.send('c received')
    socket.receive()
    x = group.rand_int()
    hb = group.gen_pow(x)
    hb_inv = group.mul(c, group.inv(hb))
    if bool(int(bit)):
        socket.send(hb_inv)
    else:
        socket.send(hb)
    socket.receive()
    socket.send('ok')
    (e0, e1, c1, l) = socket.receive()
    socket.send('e0, e1, c1 received')

    decrypt_hash = ot_hash(group.pow(c1, x), l)
    if bool(int(bit)):
        # convert and evaluate string tuple to return (key, value) tuple
        return eval(xor_bytes(e1, decrypt_hash).decode('UTF-8'))
    else:
        return eval(xor_bytes(e0, decrypt_hash).decode('UTF-8'))
