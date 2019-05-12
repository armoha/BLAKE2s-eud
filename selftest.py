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
    ctx = BLAKE2s.blake2s_ctx()

    # 256-bit hash for testing.
    if EUDIf()(BLAKE2s.BLAKE2s_init(ctx, 32, 0, 0)):
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
            BLAKE2s.BLAKE2s_update(ctx, md, outlen)  # hash the hash

            selftest_seq(key, outlen, outlen)  # keyed hash
            BLAKE2s.BLAKE2s(md, outlen, key, outlen, oin, inlen)
            BLAKE2s.BLAKE2s_update(ctx, md, outlen)  # hash the hash
            if EUDIf()(i >= 2):  # TODO
                f_setcurpl(f_getuserplayerid())
                s.insert(0, i, ", ", j, ": ")
                for z in EUDLoopRange(8):
                    s.append(hptr(f_dwread_epd(EPD(md) + z)), " ")
                s.Display()
            EUDEndIf()

            EUDSetContinuePoint()
            j += 1
        EUDEndWhile()
        EUDSetContinuePoint()
        i += 1
    EUDEndWhile()

    # Compute and compare the hash of hashes.
    BLAKE2s.BLAKE2s_final(ctx, md)

    if EUDIf()(Always()):  # TODO
        f_setcurpl(f_getuserplayerid())
        s.insert(0)
        for z in EUDLoopRange(8):
            s.append(hptr(f_dwread_epd(EPD(md) + z)), " ")
        s.Display()
    EUDEndIf()
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
