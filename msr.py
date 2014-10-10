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


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description='read/write magnetic stripe cards using'
                                     ' MSR805 compatible reader/writer')
    parser.add_argument('tty', metavar='TTY', type=str,
                        help='the path to the tty of the reader/writer')
    parser.add_argument('--pretend', '-p', dest='pretend', action='store_const',
                        const=bool, default=False,
                        help=('don\'t actually perform any writes, just show what would'
                              ' be done'))

    parser.add_argument('--read', '-r', dest='read_file', default=None,
                        help='read a card into the specified file')
    parser.add_argument('--write', '-w', dest='write_file', default=None,
                        help='write a card from the specified file')
    parser.add_argument('--copy', '-c', dest='copy', action='store_const',
                        const=bool, default=False,
                        help='copy a card')

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    m = MSR(args.tty)
    print "COMMTEST: ", m.commtest()
    print; print; print

    if args.read:
        import json
        print m.read()

    print; print; print
