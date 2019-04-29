from eudplib import *

from rotate import ROR7, ROR8, ROR12, ROR16

bw1 = EUDByteWriter()
bw2 = EUDByteWriter()


class VArrayReader:
    def __init__(self):
        self._trg = Forward()
        self._fin = Forward()

    def _maketrg(self):
        PushTriggerScope()
        self._trg << RawTrigger(
            nextptr=0,
            actions=[
                SetMemory(0, SetTo, 0),
                SetNextPtr(0, self._fin),
            ]
        )
        self._fin << RawTrigger(
            actions=[
                SetMemory(self._trg + 4, Add, 72),
                SetMemory(self._trg + 328 + 16, Add, 18),
                SetMemory(self._trg + 360 + 16, Add, 18),
            ]
        )
        PopTriggerScope()

    def seek(self, varr_ptr, varr_epd, eudv, acts=[]):
        if not self._trg.IsSet():
            self._maketrg()

        if IsEUDVariable(varr_ptr):
            nptr = Forward()
            RawTrigger(
                nextptr=varr_ptr.GetVTable(),
                actions=[
                    varr_ptr.QueueAssignTo(EPD(self._trg) + 1),
                    SetNextPtr(varr_ptr.GetVTable(), varr_epd.GetVTable()),
                    varr_epd.AddNumber(1),
                    varr_epd.QueueAssignTo(EPD(self._trg) + 360 // 4 + 4),
                    SetNextPtr(varr_epd.GetVTable(), nptr),
                    SetMemory(self._trg + 328 + 20, SetTo, EPD(eudv.getValueAddr())),
                ]
            )
            nptr << NextTrigger()
            VProc(varr_epd, [
                varr_epd.AddNumber(328 // 4 + 3),
                SetMemory(varr_epd._varact + 16, Add, -8),
                [acts],
            ])
        else:
            return [
                SetNextPtr(self._trg, varr_ptr),
                SetMemory(self._trg + 328 + 16, SetTo, varr_epd + 328 // 4 + 4),
                SetMemory(self._trg + 328 + 20, SetTo, EPD(eudv.getValueAddr())),
                SetMemory(self._trg + 360 + 16, SetTo, varr_epd + 1),
            ]

    def read(self, acts=[]):
        if not self._trg.IsSet():
            self._maketrg()
        nptr = Forward()
        RawTrigger(
            nextptr=self._trg,
            actions=[
                SetNextPtr(self._fin, nptr),
                [acts],
            ]
        )
        nptr << NextTrigger()


def EUDFor(var, start, cond, incr):
    EUDCreateBlock("eudforblock", None)

    v = var
    v << start
    if EUDWhile()(v <= cond):
        yield v
        EUDSetContinuePoint()
        v += incr
    EUDEndWhile()
    EUDPopBlock("eudforblock")


vr = VArrayReader()
ctx_b = EUDArray(16)
ctx_h = EUDVArray(8)()
ctx_t = EUDVArray(2)()
ctx_c = EUDVariable()
ctx_outlen = EUDVariable()


# Initialization Vector.
# fmt: off
blake2s_iv = [
    0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
    0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19,
]
sigma = EUDVArray(160)([
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3,
    11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4,
    7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8,
    9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13,
    2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9,
    12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11,
    13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10,
    6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5,
    10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0,
])
# fmt: on


# compression function. "last" flag indicates last block.
@EUDFunc
def BLAKE2s_compress(last):
    i = EUDVariable()
    g = EUDCreateVariables(2)
    v, m = EUDVArray(16)(), EUDVArray(16)()

    for i in EUDFor(i, 0, 7, 1):
        v[i] = ctx_h[i]
    DoActions([
        [
            SetMemory(v + 328 + 20 + 72 * (k+8), SetTo, blake2s_iv[k])
            for k in range(8)
        ],
        vr.seek(sigma, EPD(sigma), g[0])
    ])

    v[12] = v[12] ^ ctx_t[0]
    v[13] = v[13] ^ ctx_t[1]
    if EUDIf()(last):
        v[14] = f_bitnot(v[14])
    EUDEndIf()

    for i in EUDFor(i, 0, 15, 1):
        m[i] = ctx_b[i]

    # Mixing function G.
    @EUDFunc
    def B2S_G(a, b, c, d, x, y):
        p = v[a] + v[b] + x
        v[a] = p
        q = f_bitxor(v[d], p)
        ROR16(q)
        v[d] = q
        r = v[c] + q
        v[c] = r
        s = f_bitxor(v[b], r)
        ROR12(s)
        v[b] = s
        t = p + s + y
        v[a] = t
        u = f_bitxor(q, t)
        ROR8(u)
        v[d] = u
        w = r + u
        v[c] = w
        z = f_bitxor(s, w)
        ROR7(z)
        v[b] = z

    if EUDLoopN()(10):
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(0, 4, 8, 12, m[g[0]], m[g[1]])
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(1, 5, 9, 13, m[g[0]], m[g[1]])
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(2, 6, 10, 14, m[g[0]], m[g[1]])
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(3, 7, 11, 15, m[g[0]], m[g[1]])
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(0, 5, 10, 15, m[g[0]], m[g[1]])
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(1, 6, 11, 12, m[g[0]], m[g[1]])
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(2, 7, 8, 13, m[g[0]], m[g[1]])
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        vr.read(SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(3, 4, 9, 14, m[g[0]], m[g[1]])
    EUDEndLoopN()

    for i in EUDFor(i, 0, 7, 1):
        ctx_h[i] = ctx_h[i] ^ (v[i] ^ v[i + 8])


# Initialize the hashing context "ctx" with optional key "key".
#      1 <= outlen <= 32 gives the digest size in bytes.
#      Secret key (also <= 32 bytes) is optional (keylen = 0).
@EUDFunc
def BLAKE2s_init(outlen, key, keylen):  # (keylen=0: no key)
    i = EUDVariable()

    if EUDIfNot()([outlen >= 1, outlen <= 32, keylen <= 32]):
        EUDReturn(-1)  # illegal parameters
    EUDEndIf()

    DoActions([
        [
            SetMemory(ctx_h + 328 + 20 + 72 * k, SetTo, blake2s_iv[k])
            for k in range(8)
        ],
        SetMemory(ctx_t + 328 + 20, SetTo, 0),
        SetMemory(ctx_t + 328 + 20 + 72, SetTo, 0),
        ctx_c.SetNumber(0),
        [
            SetMemory(ctx_b + 4 * k, SetTo, 0)
            for k in range(16)
        ]
    ])

    ctx_h[0] = ctx_h[0] ^ 0x01010000 ^ f_bitlshift(keylen, 8) ^ outlen

    ctx_outlen << outlen
    i << keylen
    if EUDIf()(keylen >= 1):
        BLAKE2s_update(key, keylen)
        ctx_c << 64
    EUDEndIf()

    EUDReturn(0)


# Add "inlen" bytes from "oin" into the hash.
@EUDFunc
def BLAKE2s_update(oin, inlen):
    if EUDIf()(inlen == 0):
        EUDReturn()
    EUDEndIf()
    global ctx_c
    i = EUDVariable()

    i << 0
    bw1.seekoffset(oin)
    bw2.seekoffset(ctx_b + ctx_c)
    if EUDWhile()(i < inlen):
        if EUDIf()(ctx_c == 64):
            ctx_t[0] += ctx_c
            if EUDIf()(ctx_t[0] < ctx_c):
                ctx_t[1] += 1
            EUDEndIf()
            BLAKE2s_compress(0)
            ctx_c << 0
            bw2.flushdword()
            bw2.seekoffset(ctx_b)
        EUDEndIf()
        b = bw1.readbyte()
        bw2.writebyte(b)
        ctx_c += 1
        EUDSetContinuePoint()
        i += 1
    EUDEndWhile()
    bw2.flushdword()
    EUDReturn()


def BLAKE2s_final(out):
    global ctx_c
    i = EUDVariable()
    ctx_t[0] += ctx_c
    if EUDIf()(ctx_t[0] < ctx_c):
        ctx_t[1] += 1
    EUDEndIf()

    bw1.seekoffset(ctx_b + ctx_c)
    if EUDWhile()(ctx_c <= 63):
        bw1.writebyte(0)
        ctx_c += 1
    EUDEndWhile()
    bw1.flushdword()
    BLAKE2s_compress(1)

    # little endian convert and store
    v = EUDVariable()
    DoActions([i.SetNumber(0), vr.seek(ctx_h, EPD(ctx_h), v)])
    bw1.seekoffset(out)
    if EUDWhile()(i < ctx_outlen):
        vr.read()
        b0, b1, b2, b3 = f_dwbreak(v)[2:6]
    
        bw1.writebyte(b0)
        i += 1
        EUDBreakIf(i >= ctx_outlen)
    
        bw1.writebyte(b1)
        i += 1
        EUDBreakIf(i >= ctx_outlen)
    
        bw1.writebyte(b2)
        i += 1
        EUDBreakIf(i >= ctx_outlen)
    
        bw1.writebyte(b3)
        i += 1
    EUDEndWhile()
    bw1.flushdword()


# Convenience function for all-in-one computation.
@EUDFunc
def BLAKE2s(out, outlen, key, keylen, oin, inlen):
    if EUDIf()(BLAKE2s_init(outlen, key, keylen)):
        EUDReturn(-1)
    EUDEndIf()
    BLAKE2s_update(oin, inlen)
    BLAKE2s_final(out)

    EUDReturn(0)
