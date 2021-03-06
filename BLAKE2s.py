from eudplib import *

from rotate import ROR7, ROR8, ROR12, ROR16

bw1 = EUDByteWriter()
bw2 = EUDByteWriter()


class blake2s_ctx(EUDStruct):
    _fields_ = [
        ("b", EUDArray),
        ("h", EUDVArray(8)),
        ("t", EUDVArray(2)),
        "c",
        "outlen",
    ]

    def constructor(self, b=None, h=None, t=None):
        if b is None:
            self.b = EUDArray(16)
        if h is None:
            self.h = EUDVArray(8)()
        if t is None:
            self.t = EUDVArray(2)()


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


vr = EUDVArrayReader()
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


@EUDFunc
def BLAKE2s_compress(ctx, last):
    """Compression function. "last" flag indicates last block."""
    ctx = blake2s_ctx.cast(ctx)
    i = EUDVariable()
    g = EUDCreateVariables(2)
    v, m = EUDVArray(16)(), EUDVArray(16)()

    for i in EUDFor(i, 0, 7, 1):
        v[i] = ctx.h[i]
    DoActions(
        [SetMemory(v + 328 + 20 + 72 * (k + 8), SetTo, blake2s_iv[k]) for k in range(8)]
        + [vr.seek(sigma, EPD(sigma), g[0])]
    )

    v[12] = v[12] ^ ctx.t[0]
    v[13] = v[13] ^ ctx.t[1]
    if EUDIf()(last):
        v[14] = f_bitnot(v[14])
    EUDEndIf()

    for i in EUDFor(i, 0, 15, 1):
        m[i] = ctx.b[i]

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
        PushTriggerScope()
        update_g0 = vr.read(
            SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr()))
        )
        update_g1 = vr.read(
            SetMemory(vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr()))
        )
        PopTriggerScope()

        def update_g():
            nptr = Forward()
            RawTrigger(
                nextptr=update_g0, actions=SetMemory(update_g1 + 380, SetTo, nptr)
            )
            nptr << NextTrigger()

        update_g()
        B2S_G(0, 4, 8, 12, m[g[0]], m[g[1]])
        update_g()
        B2S_G(1, 5, 9, 13, m[g[0]], m[g[1]])
        update_g()
        B2S_G(2, 6, 10, 14, m[g[0]], m[g[1]])
        update_g()
        B2S_G(3, 7, 11, 15, m[g[0]], m[g[1]])
        update_g()
        B2S_G(0, 5, 10, 15, m[g[0]], m[g[1]])
        update_g()
        B2S_G(1, 6, 11, 12, m[g[0]], m[g[1]])
        update_g()
        B2S_G(2, 7, 8, 13, m[g[0]], m[g[1]])
        update_g()
        B2S_G(3, 4, 9, 14, m[g[0]], m[g[1]])
    EUDEndLoopN()

    for i in EUDFor(i, 0, 7, 1):
        ctx.h[i] = ctx.h[i] ^ (v[i] ^ v[i + 8])


@EUDFunc
def BLAKE2s_init(ctx, outlen, key, keylen):
    """
    Initialize the hashing context "ctx" with optional key "key".

    1 <= outlen <= 32 gives the digest size in bytes.
    Secret key (also <= 32 bytes) is optional (keylen=0: no key).
    """
    origcp = f_getcurpl()
    ctx = blake2s_ctx.cast(ctx)
    i = EUDVariable()

    if EUDIfNot()([outlen >= 1, outlen <= 32, keylen <= 32]):
        EUDReturn(-1)  # illegal parameters
    EUDEndIf()

    ctx_h, ctx_t, ctx_b = EPD(ctx.h), EPD(ctx.t), EPD(ctx.b)
    VProc(
        ctx_h, [ctx_h.QueueAddTo(EPD(0x6509B0)), SetMemory(0x6509B0, SetTo, 348 // 4)]
    )
    VProc(
        ctx_t,
        [
            ctx_t.QueueAddTo(EPD(0x6509B0)),
            SetDeaths(CurrentPlayer, SetTo, blake2s_iv[0], 0),
            SetDeaths(CurrentPlayer, SetTo, blake2s_iv[2], 3),
            SetDeaths(CurrentPlayer, SetTo, blake2s_iv[4], 6),
            SetDeaths(CurrentPlayer, SetTo, blake2s_iv[6], 9),
            SetMemory(0x6509B0, Add, 18),
            SetDeaths(CurrentPlayer, SetTo, blake2s_iv[1], 0),
            SetDeaths(CurrentPlayer, SetTo, blake2s_iv[3], 3),
            SetDeaths(CurrentPlayer, SetTo, blake2s_iv[5], 6),
            SetDeaths(CurrentPlayer, SetTo, blake2s_iv[7], 9),
            SetMemory(0x6509B0, SetTo, 348 // 4),
        ],
    )
    VProc(
        ctx_b,
        [
            ctx_b.QueueAssignTo(EPD(0x6509B0)),
            SetDeaths(CurrentPlayer, SetTo, 0, 0),
            SetMemory(0x6509B0, Add, 18),
            SetDeaths(CurrentPlayer, SetTo, 0, 0),
        ],
    )
    VProc(
        origcp,
        [origcp.QueueAssignTo(EPD(0x6509B0))]
        + [
            [
                SetDeaths(CurrentPlayer, SetTo, 0, 0),
                SetDeaths(CurrentPlayer, SetTo, 0, 1),
                SetMemory(0x6509B0, Add, 1),
            ]
            for k in range(4)
        ]
        + [
            [SetDeaths(CurrentPlayer, SetTo, 0, 0), SetMemory(0x6509B0, Add, 1)]
            for k in range(7)
        ]
        + [SetDeaths(CurrentPlayer, SetTo, 0, 0)],
    )
    ctx.h[0] = ctx.h[0] ^ 0x01010000 ^ f_bitlshift(keylen, 8) ^ outlen
    ctx.c = 0
    ctx.outlen = outlen
    i << keylen
    if EUDIf()(keylen >= 1):
        BLAKE2s_update(ctx, key, keylen)
        ctx.c = 64
    EUDEndIf()

    EUDReturn(0)


@EUDFunc
def BLAKE2s_update(ctx, oin, inlen):
    """Add "inlen" bytes from "oin" into the hash."""
    ctx = blake2s_ctx.cast(ctx)
    if EUDIf()(inlen == 0):
        EUDReturn()
    EUDEndIf()
    i = EUDVariable()

    i << 0
    ctx_b = ctx.b
    bw1.seekoffset(oin)
    bw2.seekoffset(ctx_b + ctx.c)
    if EUDWhile()(i < inlen):
        ctx_c = ctx.c
        if EUDIf()(ctx_c == 64):
            ctx_t0 = ctx.t[0] + ctx_c
            ctx.t[0] = ctx_t0
            if EUDIf()(ctx_t0 < ctx_c):
                ctx.t[1] += 1
            EUDEndIf()
            BLAKE2s_compress(ctx, 0)
            ctx.c = 0
            bw2.flushdword()
            bw2.seekoffset(ctx_b)
        EUDEndIf()
        b = bw1.readbyte()
        bw2.writebyte(b)
        ctx.c += 1
        EUDSetContinuePoint()
        i += 1
    EUDEndWhile()
    bw2.flushdword()


@EUDFunc
def BLAKE2s_final(ctx, out):
    ctx = blake2s_ctx.cast(ctx)
    i = EUDVariable()
    ctx_c = ctx.c
    ctx_t0 = ctx.t[0] + ctx_c
    ctx.t[0] = ctx_t0
    if EUDIf()(ctx_t0 < ctx_c):
        ctx.t[1] += 1
    EUDEndIf()

    bw1.seekoffset(ctx.b + ctx_c)
    if EUDWhile()(ctx.c <= 63):
        bw1.writebyte(0)
        ctx.c += 1
    EUDEndWhile()
    bw1.flushdword()
    BLAKE2s_compress(ctx, 1)

    # little endian convert and store
    v = EUDVariable()
    i << 0
    ctx_h = ctx.h
    vr.seek(ctx_h, EPD(ctx_h), v)
    bw1.seekoffset(out)
    ctx_outlen = ctx.outlen
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


@EUDFunc
def BLAKE2s(out, outlen, key, keylen, oin, inlen):
    """Compute hash by all-in-one function for convenience."""
    ctx = blake2s_ctx()
    if EUDIf()(BLAKE2s_init(ctx, outlen, key, keylen)):
        EUDReturn(-1)
    EUDEndIf()
    BLAKE2s_update(ctx, oin, inlen)
    BLAKE2s_final(ctx, out)

    EUDReturn(0)
