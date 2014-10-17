#!/usr/bin/env python
import serial
import datetime
import json


ESCAPE = "\x1b"


class ParseError(Exception):
    pass


class ReadTimeoutException(BaseException):
    pass


class StatusError(BaseException):
    pass


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

    def do_with_status(self, command, timeout=5):
        print "command: %s" % command.encode('hex')
        self.reset()
        self.serial.write(command)
        data = ""
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
        while datetime.datetime.now() < end_time:
            data += self.serial.read(100)

            if len(data) >= 2 and data[-2] == ESCAPE and data[-1] in '01249':
                status = int(data[-1])
                print "         %s" % data.encode('hex')
                return data[:-2], status

        self.reset()
        print "DATA: %s" % data.encode('hex')
        raise ReadTimeoutException("Timed out waiting for status")

    def read(self):
        d, status = self.do_with_status(ESCAPE + 'r')
        if status:
            raise StatusError(status)
        parts = d.split(ESCAPE)
        for i, part in enumerate(parts):
            print i, [hex(ord(x)) for x in part], part
        return parts

    def write(self, data):
        d, status = self.do_with_status(ESCAPE + 'w' + data)
        print "write (%s) status: %d " % (data.encode('hex'), status)

    def read_tracks(self):
        parts = self.read()
        if parts[1] != "s":
            raise ParseError("First part should be 's'")
        if parts[-1][-1] != '\x1c':
            raise ParseError("Last byte of track-3 should be '\\x1c'")

        tracks = [''] * 4
        for part in parts[2:]:
            if part[0] in ["\x01", "\x02", "\x03"]:
                tracks[ord(part[0])] = part[2:]
        for i in range(1, 4):
            print "track %d: %s" % (i, tracks[i])

        if len(tracks[3]) and tracks[3][-1] == '\x1c':
            tracks[3] = tracks[3][:-1]
        return tracks

    def write_tracks(self, tracks):
        data = ESCAPE + 's'
        for i in range(1, 4):
            data += ESCAPE + chr(i) + tracks[i].replace('\x3f', '')
        data += '\x3f\x1c'
        self.write(data)


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description='read/write magnetic stripe cards using'
                                     ' MSR805 compatible reader/writer')
    parser.add_argument('tty', metavar='TTY', type=str, default=None, nargs="?",
                        help='the path to the tty of the reader/writer')
    parser.add_argument('--pretend', '-p', dest='pretend', action='store_const',
                        const=bool, default=False,
                        help=('don\'t actually perform any writes, just show what would'
                              ' be done'))

    parser.add_argument('--read', '-r', dest='read_file', default=None,
                        help='read track data from a card into the specified file')
    parser.add_argument('--write', '-w', dest='write_file', default=None,
                        help='write a card from the specified file')
    parser.add_argument('--copy', '-c', dest='copy', action='store_const',
                        const=bool, default=False,
                        help='copy a card')

    args = parser.parse_args()
    return args


def detect_device():
    import glob
    import platform

    if platform.uname()[0] == "Darwin":
        ttys = glob.glob("/dev/tty.usb*")
    elif platform.uname()[0] == "Linux":
        ttys = glob.glob("/dev/ttyUSB*")

    for tty in ttys:
        m = MSR(tty)
        if m.commtest():
            return m

    return None


def main():
    args = parse_args()

    m = None
    if args.tty:
        m = MSR(args.tty)
    else:
        m = detect_device()

    if not m:
        print "Couldn't find the msr device"

    if args.read_file:
        tracks = m.read_tracks()
        open(args.read_file, "w").write(json.dumps(tracks))
    elif args.write_file:
        tracks = json.loads(open(args.write_file, "rb").read())
        m.write_tracks(tracks)
    elif args.copy:
        print "Swipe source card"
        tracks = m.read_tracks()
        print tracks
        print "Now swipe destination card"
        m.write_tracks(tracks)

    print; print; print


if __name__ == '__main__':
    main()
