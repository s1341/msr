#!/usr/bin/env python
import serial


ESCAPE = "\x1b"


class MSR(object):
    def __init__(self, tty):
        self.serial = serial.Serial(tty, timeout=0.1)

    def reset(self):
        self.serial.write(ESCAPE + "a")

    def commtest(self):
        self.reset()
        self.serial.write(ESCAPE + "e")
        d = self.serial.read(2)
        return d == ESCAPE + "y"

    def read(self):
        self.reset()
        self.serial.write(ESCAPE + "r")

        attempts = 100
        d = ""
        while attempts:
            c = self.serial.read(1)
            if len(c):
                d += c
            attempts -= 1

        print d[0] == ESCAPE, hex(len(d)), [hex(ord(x)) for x in d]
        print d
        self.reset()

        parts = d.split(ESCAPE)
        i = 0
        for part in parts:
            print i, [hex(ord(x)) for x in part], part
            i += 1
        return d


if __name__ == '__main__':
    import sys
    m = MSR(sys.argv[1])
    print "COMMTEST: ", m.commtest()

    print m.read()
