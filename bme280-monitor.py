#!/usr/bin/env python3
# file: bme280-monitor.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Copyright © 2018 R.F. Smith <rsmith@xs4all.nl>.
# SPDX-License-Identifier: MIT
# Created: 2018-04-22T20:56:36+0200
# Last modified: 2018-04-28T01:08:30+0200
"""
Monitoring program for the Bosch BME280 temperature, pressure and humidity sensor.
The sensor is connected to the computer via an FT232H using SPI.

Connect 5V and ground from the FT232H to their respective pins on the BMP280.
Then connect D0 to SCK, D1 to SDI, D2 to SDO and e.g. D3 to CS.
You can use the -c or --cs option to choose another chip select line.
"""

from datetime import datetime
from enum import IntEnum
import argparse
import sys
import time

from pyftdi.spi import SpiController
from bme280 import Bme280spi

__version__ = '1.0'


class Port(IntEnum):
    # Generic names
    ADBUS3 = 0
    ADBUS4 = 1
    ADBUS5 = 2
    ADBUS6 = 3
    ADBUS7 = 4
    # Adafruit FT232H breakout
    D3 = 0
    D4 = 1
    D5 = 2
    D6 = 3
    D7 = 4


def main(argv):
    """
    Entry point for bme280-monitor.py

    Arguments:
        argv: command line arguments
    """

    now = datetime.utcnow().strftime('%FT%TZ')
    args = process_arguments(argv)

    # Connect to the sensor.
    ctrl = SpiController()
    ctrl.configure('ftdi://ftdi:232h/{}'.format(args.device))
    spi = ctrl.get_port(Port[args.cs].value)
    spi.set_frequency(args.prequency)
    bme280 = Bme280spi(spi)

    # Open the data file.
    datafile = open(args.path.format(now), 'w')

    # Write datafile header.
    datafile.write('# BME280 data.\n# Started monitoring at {}.\n'.format(now))
    datafile.write('# Per line, the data items are:\n')
    datafile.write('# * UTC date and time in ISO8601 format\n')
    datafile.write('# * Temperature in °C\n')
    datafile.write('# * Pressure in Pa\n')
    datafile.write('# * Relative humidity in %.\n')
    datafile.flush()

    # Read and write the data.
    try:
        while True:
            now = datetime.utcnow().strftime('%FT%TZ')
            temperature, pressure, humidity = bme280.read()
            line = '{} {:.2f} {:.0f} {:.2f}\n'.format(now, temperature, pressure, humidity)
            datafile.write(line)
            datafile.flush()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        sys.exit(1)


def process_arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-c',
        '--cs',
        default="D3",
        type=str,
        help='FT232 pin to use for SPI chip select (default D3, range D3 - D7).'
    )
    parser.add_argument(
        '-d',
        '--device',
        default=1,
        type=int,
        help='FT232 device number (default 1 for FT232*, 1 or 2 for 2232*, 1-4 for 4232* devices).'
    )
    parser.add_argument(
        '-f',
        '--frequency',
        default=100000,
        type=int,
        help='SPI bus requency in Hz (default 100000 Hz, must be >91 Hz and <6 MHz).'
    )
    parser.add_argument(
        '-i',
        '--interval',
        default=5,
        type=int,
        help='interval between measurements (≥5 s, default 5 s).')
    parser.add_argument(
        '-v', '--version', action='version', version=__version__)
    parser.add_argument(
        'path',
        nargs=1,
        help=r'path template for the data file. Should contain {}. '
        r'For example "/tmp/bme280-{}.d"')
    args = parser.parse_args(argv)
    args.path = args.path[0]
    errormsg = None
    if not args.path or r'{}' not in args.path:
        errormsg = r'No path given or {} not in path.'
    elif args.cs not in Port.__members__:
        errormsg = 'Invalid chip select line.'
    elif args.frequency < 92:
        errormsg = 'Frequency must be between 92 Hz and 6 MHz.'
    if errormsg:
        print(errormsg + '\n')
        parser.print_help()
        sys.exit(0)
    if args.interval < 5:
        args.interval = 5
    return args


if __name__ == '__main__':
    main(sys.argv[1:])
