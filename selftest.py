from eudplib import *

import BLAKE2s

s = StringBuffer(1023)
br = EUDByteReader()
bw = EUDByteWriter()


@EUDFunc
def selftest_seq(out, olen, seed):
    i = EUDVariable()
    t, a, b = EUDCreateVariables(3)

    bw.seekoffset(out)
    Trigger(actions=[a.SetNumber(0xDEAD4BAD * seed), b.SetNumber(1), i.SetNumber(0)])
    if EUDWhile()(i < olen):
        t << a + b
        a << b
        b << t
        bw.writebyte(f_bitrshift(t, 24) & 0xFF)
        EUDSetContinuePoint()
        i += 1
    EUDEndWhile()
    bw.flushdword()


# BLAKE2s self-test validation. Return 0 when OK.
@EUDFunc
def blake2s_selftest():
    # Grand hash of hash results.
    # fmt: off
    blake2s_res = Db(
        bytearray(
            [
                0x6A, 0x41, 0x1F, 0x08, 0xCE, 0x25, 0xAD, 0xCD,
                0xFB, 0x02, 0xAB, 0xA6, 0x41, 0x45, 0x1C, 0xEC,
                0x53, 0xC5, 0x98, 0xB2, 0x4F, 0x4F, 0xC7, 0x87,
                0xFB, 0xDC, 0x88, 0x79, 0x7F, 0x4C, 0x1D, 0xFE,
            ]
        )
    )
    # fmt: on
    # Parameter sets.
    b2s_md_len = EUDVArray(4)([16, 20, 28, 32])
    b2s_in_len = EUDVArray(6)([0, 3, 64, 65, 255, 1024])

    i, j, outlen, inlen = EUDCreateVariables(4)
    oin, md, key = Db(1024), Db(32), Db(32)

    # 256-bit hash for testing.
    if EUDIf()(selftest_BLAKE2s_init(32, 0, 0)):
        EUDReturn(-1)
    EUDEndIf()

    i << 0
    if EUDWhile()(i <= 3):
        outlen = b2s_md_len[i]
        j << 0
        if EUDWhile()(j <= 5):
            inlen = b2s_in_len[j]

            selftest_seq(oin, inlen, inlen)  # unkeyed hash
            BLAKE2s.BLAKE2s(md, outlen, 0, 0, oin, inlen)
            selftest_BLAKE2s_update(md, outlen)  # hash the hash

            selftest_seq(key, outlen, outlen)  # keyed hash
            BLAKE2s.BLAKE2s(md, outlen, key, outlen, oin, inlen)
            selftest_BLAKE2s_update(md, outlen)  # hash the hash

            EUDSetContinuePoint()
            j += 1
        EUDEndWhile()
        EUDSetContinuePoint()
        i += 1
    EUDEndWhile()

    # Compute and compare the hash of hashes.
    selftest_BLAKE2s_final(md)

    i << 0
    br.seekepd(EPD(md))
    bw.seekepd(EPD(blake2s_res))
    if EUDWhile()(i <= 31):
        if EUDIf()(br.readbyte() != bw.readbyte()):
            EUDReturn(-1)
        EUDEndIf()
        EUDSetContinuePoint()
        i += 1
    EUDEndWhile()

    EUDReturn(0)


# Test driver
def onPluginStart():
    result = EUDTernary(blake2s_selftest())(EPD(Db("FAIL")))(EPD(Db("OK")))
    f_setcurpl(f_getuserplayerid())
    s.print("blake2s_selftest() = ", epd2s(result))


ctx_b = EUDArray(16)
ctx_h = EUDVArray(8)()
ctx_t = EUDVArray(2)()
ctx_c = EUDVariable()
ctx_outlen = EUDVariable()


@EUDFunc
def selftest_BLAKE2s_compress(last):
    i = EUDVariable()
    g = EUDCreateVariables(2)
    v, m = EUDVArray(16)(), EUDVArray(16)()

    for i in BLAKE2s.EUDFor(i, 0, 7, 1):
        v[i] = ctx_h[i]
    DoActions([
        [
            SetMemory(v + 328 + 20 + 72 * (k+8), SetTo, BLAKE2s.blake2s_iv[k])
            for k in range(8)
        ],
        BLAKE2s.vr.seek(BLAKE2s.sigma, EPD(BLAKE2s.sigma), g[0])
    ])

    v[12] = v[12] ^ ctx_t[0]
    v[13] = v[13] ^ ctx_t[1]
    if EUDIf()(last):
        v[14] = f_bitnot(v[14])
    EUDEndIf()

    for i in BLAKE2s.EUDFor(i, 0, 15, 1):
        m[i] = ctx_b[i]

    # Mixing function G.
    @EUDFunc
    def B2S_G(a, b, c, d, x, y):
        p = v[a] + v[b] + x
        v[a] = p
        q = f_bitxor(v[d], p)
        BLAKE2s.ROR16(q)
        v[d] = q
        r = v[c] + q
        v[c] = r
        s = f_bitxor(v[b], r)
        BLAKE2s.ROR12(s)
        v[b] = s
        t = p + s + y
        v[a] = t
        u = f_bitxor(q, t)
        BLAKE2s.ROR8(u)
        v[d] = u
        w = r + u
        v[c] = w
        z = f_bitxor(s, w)
        BLAKE2s.ROR7(z)
        v[b] = z

    if EUDLoopN()(10):
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(0, 4, 8, 12, m[g[0]], m[g[1]])
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(1, 5, 9, 13, m[g[0]], m[g[1]])
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(2, 6, 10, 14, m[g[0]], m[g[1]])
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(3, 7, 11, 15, m[g[0]], m[g[1]])
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(0, 5, 10, 15, m[g[0]], m[g[1]])
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(1, 6, 11, 12, m[g[0]], m[g[1]])
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(2, 7, 8, 13, m[g[0]], m[g[1]])
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[0].getValueAddr())))
        BLAKE2s.vr.read(SetMemory(BLAKE2s.vr._trg + 328 + 20, SetTo, EPD(g[1].getValueAddr())))
        B2S_G(3, 4, 9, 14, m[g[0]], m[g[1]])
    EUDEndLoopN()

    for i in BLAKE2s.EUDFor(i, 0, 7, 1):
        ctx_h[i] = ctx_h[i] ^ (v[i] ^ v[i + 8])


@EUDFunc
def selftest_BLAKE2s_init(outlen, key, keylen):  # (keylen=0: no key)
    i = EUDVariable()

    if EUDIfNot()([outlen >= 1, outlen <= 32, keylen <= 32]):
        EUDReturn(-1)  # illegal parameters
    EUDEndIf()

    DoActions([
        [
            SetMemory(ctx_h + 328 + 20 + 72 * k, SetTo, BLAKE2s.blake2s_iv[k])
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
        selftest_BLAKE2s_update(key, keylen)
        ctx_c << 64
    EUDEndIf()

    EUDReturn(0)


# Add "inlen" bytes from "oin" into the hash.
@EUDFunc
def selftest_BLAKE2s_update(oin, inlen):
    if EUDIf()(inlen == 0):
        EUDReturn()
    EUDEndIf()
    global ctx_c
    i = EUDVariable()

    i << 0
    BLAKE2s.bw1.seekoffset(oin)
    BLAKE2s.bw2.seekoffset(ctx_b + ctx_c)
    if EUDWhile()(i < inlen):
        if EUDIf()(ctx_c == 64):
            ctx_t[0] += ctx_c
            if EUDIf()(ctx_t[0] < ctx_c):
                ctx_t[1] += 1
            EUDEndIf()
            selftest_BLAKE2s_compress(0)
            ctx_c << 0
            BLAKE2s.bw2.flushdword()
            BLAKE2s.bw2.seekoffset(ctx_b)
        EUDEndIf()
        b = BLAKE2s.bw1.readbyte()
        BLAKE2s.bw2.writebyte(b)
        ctx_c += 1
        EUDSetContinuePoint()
        i += 1
    EUDEndWhile()
    BLAKE2s.bw2.flushdword()
    EUDReturn()


def selftest_BLAKE2s_final(out):
    global ctx_c
    i = EUDVariable()
    ctx_t[0] += ctx_c
    if EUDIf()(ctx_t[0] < ctx_c):
        ctx_t[1] += 1
    EUDEndIf()

    BLAKE2s.bw1.seekoffset(ctx_b + ctx_c)
    if EUDWhile()(ctx_c <= 63):
        BLAKE2s.bw1.writebyte(0)
        ctx_c += 1
    EUDEndWhile()
    BLAKE2s.bw1.flushdword()
    selftest_BLAKE2s_compress(1)

    # little endian convert and store
    v = EUDVariable()
    DoActions([i.SetNumber(0), BLAKE2s.vr.seek(ctx_h, EPD(ctx_h), v)])
    BLAKE2s.bw1.seekoffset(out)
    if EUDWhile()(i < ctx_outlen):
        BLAKE2s.vr.read()
        b0, b1, b2, b3 = f_dwbreak(v)[2:6]
    
        BLAKE2s.bw1.writebyte(b0)
        i += 1
        EUDBreakIf(i >= ctx_outlen)
    
        BLAKE2s.bw1.writebyte(b1)
        i += 1
        EUDBreakIf(i >= ctx_outlen)
    
        BLAKE2s.bw1.writebyte(b2)
        i += 1
        EUDBreakIf(i >= ctx_outlen)
    
        BLAKE2s.bw1.writebyte(b3)
        i += 1
    EUDEndWhile()
    BLAKE2s.bw1.flushdword()
