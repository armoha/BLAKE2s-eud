import random

from eudplib import *

from trigutils import SetMemory3

ret = EUDVariable(0)

ROR16_start, ROR16_end = Forward(), Forward()
ROR12_start, ROR12_end = Forward(), Forward()

ROL8_start, ROL8_end = Forward(), Forward()
ROR8_start, ROR8_end = Forward(), Forward()
ROR7_start, ROR7_end = Forward(), Forward()
ROL3_start, ROL3_end = Forward(), Forward()
ROR3_start, ROR3_end = Forward(), Forward()


def ROR16_init():
    PushTriggerScope()
    ROR16_start << NextTrigger()
    for i in range(31, -1, -1):
        RawTrigger(
            conditions=DeathsX(CurrentPlayer, AtLeast, 1, 0, 2**i),
            actions=[
                # ret.AddNumber(2**((i + 16) % 32)),
                SetMemory3(ret.getValueAddr(), Add, 2**((i + 16) % 32)),
            ],
        )
    VProc(ret, SetMemory3(ret._varact + 16, SetTo, EPD(ROR16_end) + 87))
    ROR16_end << RawTrigger(
        nextptr=random.getrandbits(32),
        actions=[
            SetDeaths(CurrentPlayer, SetTo, 0, 0),
            # ret.SetNumber(0),
            SetMemory3(ret.getValueAddr(), SetTo, 0),
        ]
    )
    PopTriggerScope()


def ROR16(x):
    if not ROR16_start.IsSet():
        ROR16_init()
    if IsEUDVariable(x):
        x = x.getValueAddr()
    nptr = Forward()
    RawTrigger(
        nextptr=ROR16_start,
        actions=[
            SetMemory3(0x6509B0, SetTo, EPD(x)),
            # SetNextPtr(ROR16_end, nptr),
            SetMemory3(ROR16_end + 4, SetTo, nptr),
        ]
    )
    nptr << NextTrigger()


def ROR12_init():
    PushTriggerScope()
    ROR12_start << NextTrigger()
    for i in range(31, -1, -1):
        RawTrigger(
            conditions=DeathsX(CurrentPlayer, AtLeast, 1, 0, 2**i),
            actions=[
                # ret.AddNumber(2**((i + 20) % 32)),
                SetMemory3(ret.getValueAddr(), Add, 2**((i + 20) % 32)),
            ],
        )
    VProc(ret, SetMemory3(ret._varact + 16, SetTo, EPD(ROR12_end) + 87))
    ROR12_end << RawTrigger(
        nextptr=random.getrandbits(32),
        actions=[
            SetDeaths(CurrentPlayer, SetTo, 0, 0),
            # ret.SetNumber(0),
            SetMemory3(ret.getValueAddr(), SetTo, 0),
        ]
    )
    PopTriggerScope()


def ROR12(x):
    if not ROR12_start.IsSet():
        ROR12_init()
    if IsEUDVariable(x):
        x = x.getValueAddr()
    nptr = Forward()
    RawTrigger(
        nextptr=ROR12_start,
        actions=[
            SetMemory3(0x6509B0, SetTo, EPD(x)),
            # SetNextPtr(ROR12_end, nptr),
            SetMemory3(ROR12_end + 4, SetTo, nptr),
        ]
    )
    nptr << NextTrigger()


def ROL8_init():
    PushTriggerScope()
    ROL8_start << NextTrigger()
    for i in range(31, -1, -1):
        RawTrigger(
            conditions=DeathsX(CurrentPlayer, AtLeast, 1, 0, 2**i),
            actions=[
                # ret.AddNumber(2**((i + 8) % 32)),
                SetMemory3(ret.getValueAddr(), Add, 2**((i + 8) % 32)),
            ],
        )
    VProc(ret, SetMemory3(ret._varact + 16, SetTo, EPD(ROL8_end) + 87))
    ROL8_end << RawTrigger(
        nextptr=random.getrandbits(32),
        actions=[
            SetDeaths(CurrentPlayer, SetTo, 0, 0),
            # ret.SetNumber(0),
            SetMemory3(ret.getValueAddr(), SetTo, 0),
        ]
    )
    PopTriggerScope()


def ROL8(x):
    if not ROL8_start.IsSet():
        ROL8_init()
    if IsEUDVariable(x):
        x = x.getValueAddr()
    nptr = Forward()
    RawTrigger(
        nextptr=ROL8_start,
        actions=[
            SetMemory3(0x6509B0, SetTo, EPD(x)),
            # SetNextPtr(ROL8_end, nptr),
            SetMemory3(ROL8_end + 4, SetTo, nptr),
        ]
    )
    nptr << NextTrigger()


def ROR8_init():
    PushTriggerScope()
    ROR8_start << NextTrigger()
    for i in range(31, -1, -1):
        RawTrigger(
            conditions=DeathsX(CurrentPlayer, AtLeast, 1, 0, 2**i),
            actions=[
                # ret.AddNumber(2**((i + 24) % 32)),
                SetMemory3(ret.getValueAddr(), Add, 2**((i + 24) % 32)),
            ],
        )
    VProc(ret, SetMemory3(ret._varact + 16, SetTo, EPD(ROR8_end) + 87))
    ROR8_end << RawTrigger(
        nextptr=random.getrandbits(32),
        actions=[
            SetDeaths(CurrentPlayer, SetTo, 0, 0),
            # ret.SetNumber(0),
            SetMemory3(ret.getValueAddr(), SetTo, 0),
        ]
    )
    PopTriggerScope()


def ROR8(x):
    if not ROR8_start.IsSet():
        ROR8_init()
    if IsEUDVariable(x):
        x = x.getValueAddr()
    nptr = Forward()
    RawTrigger(
        nextptr=ROR8_start,
        actions=[
            SetMemory3(0x6509B0, SetTo, EPD(x)),
            # SetNextPtr(ROR8_end, nptr),
            SetMemory3(ROR8_end + 4, SetTo, nptr),
        ]
    )
    nptr << NextTrigger()


def ROR7_init():
    PushTriggerScope()
    ROR7_start << NextTrigger()
    for i in range(31, -1, -1):
        RawTrigger(
            conditions=DeathsX(CurrentPlayer, AtLeast, 1, 0, 2**i),
            actions=[
                # ret.AddNumber(2**((i + 25) % 32)),
                SetMemory3(ret.getValueAddr(), Add, 2**((i + 25) % 32)),
            ],
        )
    VProc(ret, SetMemory3(ret._varact + 16, SetTo, EPD(ROR7_end) + 87))
    ROR7_end << RawTrigger(
        nextptr=random.getrandbits(32),
        actions=[
            SetDeaths(CurrentPlayer, SetTo, 0, 0),
            # ret.SetNumber(0),
            SetMemory3(ret.getValueAddr(), SetTo, 0),
        ]
    )
    PopTriggerScope()


def ROR7(x):
    if not ROR7_start.IsSet():
        ROR7_init()
    if IsEUDVariable(x):
        x = x.getValueAddr()
    nptr = Forward()
    RawTrigger(
        nextptr=ROR7_start,
        actions=[
            SetMemory3(0x6509B0, SetTo, EPD(x)),
            # SetNextPtr(ROR7_end, nptr),
            SetMemory3(ROR7_end + 4, SetTo, nptr),
        ]
    )
    nptr << NextTrigger()


def ROL3_init():
    PushTriggerScope()
    ROL3_start << NextTrigger()
    for i in range(31, -1, -1):
        RawTrigger(
            conditions=DeathsX(CurrentPlayer, AtLeast, 1, 0, 2**i),
            actions=[
                # ret.AddNumber(2**((i + 3) % 32)),
                SetMemory3(ret.getValueAddr(), Add, 2**((i + 3) % 32)),
            ],
        )
    VProc(ret, SetMemory3(ret._varact + 16, SetTo, EPD(ROL3_end) + 87))
    ROL3_end << RawTrigger(
        nextptr=0,
        actions=[
            SetDeaths(CurrentPlayer, SetTo, 0, 0),
            # ret.SetNumber(0),
            SetMemory3(ret.getValueAddr(), SetTo, 0),
        ]
    )
    PopTriggerScope()


def ROL3(x):
    if not ROL3_start.IsSet():
        ROL3_init()
    if IsEUDVariable(x):
        x = x.getValueAddr()
    nptr = Forward()
    RawTrigger(
        nextptr=ROL3_start,
        actions=[
            SetMemory3(0x6509B0, SetTo, EPD(x)),
            # SetNextPtr(ROL3_end, nptr),
            SetMemory3(ROL3_end + 4, SetTo, nptr),
        ]
    )
    nptr << NextTrigger()


def ROR3_init():
    PushTriggerScope()
    ROR3_start << NextTrigger()
    for i in range(31, -1, -1):
        RawTrigger(
            conditions=DeathsX(CurrentPlayer, AtLeast, 1, 0, 2**i),
            actions=[
                # ret.AddNumber(2**((i + 29) % 32)),
                SetMemory3(ret.getValueAddr(), Add, 2**((i + 29) % 32)),
            ],
        )
    VProc(ret, SetMemory3(ret._varact + 16, SetTo, EPD(ROR3_end) + 87))
    ROR3_end << RawTrigger(
        nextptr=0,
        actions=[
            SetDeaths(CurrentPlayer, SetTo, 0, 0),
            # ret.SetNumber(0),
            SetMemory3(ret.getValueAddr(), SetTo, 0),
        ]
    )
    PopTriggerScope()


def ROR3(x):
    if not ROR3_start.IsSet():
        ROR3_init()
    if IsEUDVariable(x):
        x = x.getValueAddr()
    nptr = Forward()
    RawTrigger(
        nextptr=ROR3_start,
        actions=[
            SetMemory3(0x6509B0, SetTo, EPD(x)),
            # SetNextPtr(ROR3_end, nptr),
            SetMemory3(ROR3_end + 4, SetTo, nptr),
        ]
    )
    nptr << NextTrigger()
