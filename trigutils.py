import random

from eudplib import *

random = random.SystemRandom()


def SetMemory3(dest, modtype, value):
    modtype = EncodeModifier(modtype, issueError=True)
    unit = random.randint(0, 0xFFFF)
    epd = EPD(dest) - 12 * unit
    return Action(0, 0, 0, 0, epd, value, unit, 45, modtype, 20)
