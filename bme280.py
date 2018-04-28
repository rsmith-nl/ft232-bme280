# file: bme280.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Copyright © 2018 R.F. Smith <rsmith@xs4all.nl>.
# SPDX-License-Identifier: MIT
# Created: 2018-04-08T22:38:40+0200
# Last modified: 2018-04-28T18:25:36+0200
"""
Code to use a BME280 with FT232H using SPI or I²C connection.
Both connections use the pyftdi API.
"""

from enum import IntEnum
from time import sleep


class Reg(IntEnum):
    """Registers of the BME280."""
    ID = 0xD0
    ID_VAL = 0x60  # Contents of the ID register for a BME280.
    CTRLHUM = 0xF2
    STATUS = 0xF3
    CONTROL = 0xF4
    CONFIG = 0xF5
    TEMP_MSB = 0xFA
    PRESS_MSB = 0xF7
    HUMID_MSB = 0xFD
    # Compensation coefficient registers.
    T1 = 0x88
    T2 = 0x8A
    T3 = 0x8C
    P1 = 0x8E
    P2 = 0x90
    P3 = 0x92
    P4 = 0x94
    P5 = 0x96
    P6 = 0x98
    P7 = 0x9A
    P8 = 0x9C
    P9 = 0x9E
    H1 = 0xA1
    H2 = 0xE1
    H3 = 0xE3
    H45 = 0xE4
    H6 = 0xE7


class Bme280base:
    """Base class for BME."""

    def __init__(self):
        """Create a Bme280base instance. This is not meant to be instantiated directly.
        Use Bme280spi or Bme280i2c instead!"""
        self._temp = None
        self._press = None
        self._humid = None
        # Check if BME280
        if self._readU8(Reg.ID) != Reg.ID_VAL:
            raise RuntimeError('Not a BME280')
        # Read the compensation coefficients.
        self._dig_T1 = float(self._readU16(Reg.T1))
        self._dig_T2 = float(self._readS16(Reg.T2))
        self._dig_T3 = float(self._readS16(Reg.T3))
        self._dig_P1 = float(self._readU16(Reg.P1))
        self._dig_P2 = float(self._readS16(Reg.P2))
        self._dig_P3 = float(self._readS16(Reg.P3))
        self._dig_P4 = float(self._readS16(Reg.P4))
        self._dig_P5 = float(self._readS16(Reg.P5))
        self._dig_P6 = float(self._readS16(Reg.P6))
        self._dig_P7 = float(self._readS16(Reg.P7))
        self._dig_P8 = float(self._readS16(Reg.P8))
        self._dig_P9 = float(self._readS16(Reg.P9))
        self._dig_H1 = float(self._readU8(Reg.H1))
        self._dig_H2 = float(self._readS16(Reg.H1))
        self._dig_H3 = float(self._readU8(Reg.H3))
        E4, E5, E6 = self._readU8_3(Reg.H4)
        self._dig_H4 = float((E4 << 4) | (E5 & 0x0F))
        self._deg_H5 = float((E6 << 4) | (E5 >> 4))
        self._dig_H6 = float(self._readS8(Reg.H6))

    def _forcedmode(self):
        raise NotImplementedError

    def _readU8(self, register):
        """Read an unsigned byte from the specified register"""
        raise NotImplementedError

    def _readU8_3(self, register):
        """Read three bytes starting at the specified register"""
        raise NotImplementedError

    def _readU16(self, register):
        """Read an unsigned short from the specified register"""
        raise NotImplementedError

    def _readS16(self, register):
        """Read an unsigned short from the specified register"""
        raise NotImplementedError

    def _readU24(self, register):
        """Read the 2.5 byte temperature or pressure registers."""
        raise NotImplementedError

    @property
    def comp(self):
        """Return the compensation coefficients as a dict."""
        return {
            'dig_T1': self._dig_T1,
            'dig_T2': self._dig_T2,
            'dig_T3': self._dig_T3,
            'dig_P1': self._dig_P1,
            'dig_P2': self._dig_P2,
            'dig_P3': self._dig_P3,
            'dig_P4': self._dig_P4,
            'dig_P5': self._dig_P5,
            'dig_P6': self._dig_P6,
            'dig_P7': self._dig_P7,
            'dig_P8': self._dig_P8,
            'dig_P9': self._dig_P9,
            'dig_H1': self._dig_H1,
            'dig_H2': self._dig_H2,
            'dig_H3': self._dig_H3,
            'dig_H4': self._dig_H4,
            'dig_H5': self._dig_H5,
            'dig_H6': self._dig_H5
        }

    @property
    def temperature(self):
        """The last measured temperature in °C."""
        return self._temp

    @property
    def pressure(self):
        """The last measured pressure in Pascal."""
        return self._press

    @property
    def mbar(self):
        """The last measured pressure in mbar"""
        return 1000 * (self._press / 1.013e2)

    @property
    def humidity(self):
        """The last measured relative humidity in %."""
        return self._humid

    def read(self):
        """Read the sensor data from the chip and return (temperature, pressure, humidity)."""
        # Do one measurement in high resolution, forced mode.
        self._forcedmode()
        # Wait while measurement is running
        while self._readU8(Reg.STATUS) != 0:
            sleep(0.01)
        # Now read and process temperature.
        UT = self._readU24(Reg.TEMP_MSB)
        # print("DEBUG: UT = ", UT)
        var1 = (UT / 16384.0 - self._dig_T1 / 1024.0) * self._dig_T2
        # print("DEBUG: var1 = ", var1)
        var2 = ((UT / 131072.0 - self._dig_T1 / 8192.0) *
                (UT / 131072.0 - self._dig_T1 / 8192.0)) * self._dig_T3
        # print("DEBUG: var2 = ", var2)
        t_fine = int(var1 + var2)
        # print("DEBUG: t_fine = ", t_fine)
        self._temp = t_fine / 5120.0
        # print("DEBUG: self._temp = ", self._temp)
        # Read and process pressure.
        UP = self._readU24(Reg.PRESS_MSB)
        # print("DEBUG: UP = ", UP)
        var1 = t_fine / 2.0 - 64000.0
        # print("DEBUG: var1 = ", var1)
        var2 = var1 * var1 * self._dig_P6 / 32768.0
        # print("DEBUG: var2 = ", var2)
        var2 = var2 + var1 * self._dig_P5 * 2.0
        # print("DEBUG: var2 = ", var2)
        var2 = var2 / 4.0 + self._dig_P4 * 65536.0
        # print("DEBUG: var2 = ", var2)
        var1 = (self._dig_P3 * var1 * var1 / 534288.0 + self._dig_P2 * var1
                ) / 534288.0
        # print("DEBUG: var1 = ", var1)
        var1 = (1.0 + var1 / 32768.0) * self._dig_P1
        # print("DEBUG: var1 = ", var1)
        if var1 == 0.0:
            return 0
        p = 1048576.0 - UP
        # print("DEBUG: p = ", p)
        p = ((p - var2 / 4096.0) * 6250) / var1
        # print("DEBUG: p = ", p)
        var1 = self._dig_P9 * p * p / 2147483648.0
        # print("DEBUG: var1 = ", var1)
        var2 = p * self._dig_P8 / 32768.0
        # print("DEBUG: var2 = ", var2)
        p = p + (var1 + var2 + self._dig_P7) / 16.0
        self._press = p
        # print("DEBUG: self._press = ", self._press)
        # Read and process the relative humidity
        adc_H = self._readU16(Reg.HUMID_MSB)
        var_H = t_fine - 76800.0
        var_H = ((adc_H - (self._dig_H4 * 64.0 + self._dig_H5 / 16384.0 * var_H)) *
                 (self._dig_H2 / 65536.0 * (1.0 + self._dig_H6 / 67108864 * var_H *
                                            (1.0 + self._dig_H3 / 67108864.0 * var_H))))
        var_H = var_H * (1.0 - self._dig_H1 * var_H / 524288.0)
        if var_H > 100.0:
            var_H = 100.0
        elif var_H < 0.0:
            var_H = 0.0
        self._humid = var_H
        return (self._temp, self._press, self._humid)


class Bme280spi(Bme280base):
    """Class to use a BME280 over SPI."""

    def __init__(self, spi):
        """Create a Bme280spi instance.

        Arguments:
            spi: SpiPort.

        >> from pyftdi.spi import SpiController
        >> from bme280 import Bme280spi
        >> ctrl = SpiController()
        >> ctrl.configure('ftdi://ftdi:232h/1')
        >> spi = ctrl.get_port(0)
        >> spi.set_frequency(1000000)
        >> bme280 = Bme280spi(spi)

        N.B: port 0 is pin D3 on the Adafruit FT232H. Only pins D3-D7 can be
        used as chip select! So you can connect at most 5 spi devices to the
        FT232H.
        """
        self._spi = spi
        super(Bme280spi, self).__init__()

    def _forcedmode(self):
        """Set the sensor to forced mode."""
        self._spi.exchange([Reg.CTRLHUM & ~0x80, 0x87])
        self._spi.exchange([Reg.CONTROL & ~0x80, 0xFE])

    def _readU8(self, register):
        """Read an unsigned byte from the specified register"""
        return self._spi.exchange([register | 0x80], 1)[0]

    def _readU8_3(self, register):
        """Read three bytes starting at the specified register"""
        return self._spi.exchange([register | 0x80], 3)

    def _readU16(self, register):
        """Read an unsigned short from the specified register"""
        data = self._spi.exchange([register | 0x80], 2)
        return data[1] << 8 | data[0]

    def _readS16(self, register):
        """Read an unsigned short from the specified register"""
        result = self._readU16(register)
        if result > 32767:
            result -= 65536
        return result

    def _readU24(self, register):
        """Read the 2.5 byte temperature or pressure registers."""
        data = self._spi.exchange([register | 0x80], 3)
        rv = float((data[0] << 16 | data[1] << 8 | data[2]) >> 4)
        return rv


class Bme280i2c(Bme280base):
    """Class to use a BME280 over I²C."""

    def __init__(self, i2c):
        """Create a Bme280i2c instance.

        Arguments:
            i2c: i2cPort.

        >> from pyftdi.i2c import I2cController
        >> from bme280 import Bme280i2c
        >> ctrl = I2cController()
        >> ctrl.configure('ftdi://ftdi:232h/1')
        >> i2c = ctrl.get_port(0x77)
        >> bme280 = Bme280i2c(i2c)

        N.B: On the Adafruit breakout board, SDO is pulled high by default.
        So the default I²C address is 0x77. The port address will be 0x76
        if SDO is pulled low.
        """
        self._i2c = i2c
        super(Bme280i2c, self).__init__()

    def _forcedmode(self):
        """Set the sensor to forced mode."""
        self._spi.write_to(Reg.CTRLHUM, b'\x87')
        self._i2c.write_to(Reg.CONTROL, b'\xfe')

    def _readU8(self, register):
        """Read an unsigned byte from the specified register"""
        return self._i2c.read_from(register, 1)[0]

    def _readU8_3(self, register):
        """Read three bytes starting at the specified register"""
        return self._i2c.read_from(register, 3)

    def _readU16(self, register):
        """Read an unsigned short from the specified register"""
        data = self._i2c.read_from(register, 2)
        return data[1] << 8 | data[0]

    def _readS16(self, register):
        """Read an unsigned short from the specified register"""
        result = self._readU16(register)
        if result > 32767:
            result -= 65536
        return result

    def _readU24(self, register):
        """Read the 2.5 byte temperature or pressure registers."""
        data = self._i2c.read_from(register, 3)
        rv = float((data[0] << 16 | data[1] << 8 | data[2]) >> 4)
        return rv
