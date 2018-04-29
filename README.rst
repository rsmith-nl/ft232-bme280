Reading temperature, pressure and relative humidity with a BME280 and an FT232H
###############################################################################

:date: 2018-04-28
:tags: BME280, FT232H, Python3
:author: Roland Smith

.. Last modified: 2018-04-29T15:24:18+0200


Introduction
------------

This code was written to get the Adafruit BME280 breakout board to work with
my computer, using an Adafruit FT232H breakout board as a USB ↔ SPI or USB
↔ I²C bridge.

The ``bme280.py`` module supports both SPI and I²C connections between the
FT232H and the BME280. If uses pyftdi_ to handle those connections. This
module in turn requires pyserial_ and pyusb_. The advantage of ``pyftdi`` is
that it is a pure python solution. It does not require native libraries which
makes installing it easier.

.. _pyftdi: https://github.com/eblot/pyftdi
.. _pyusb: https://github.com/pyusb/pyusb
.. _pyserial: https://github.com/pyserial/pyserial

Additionally, there is a program called ``bme280-monitor-spi.py`` that can query
the data from the sensor at a configurable interval and write it to a file.

This code is based on similar code I wrote for the BMP280. I have used the
datasheet for the sensor, the Bosch code on github and the Adafruit
CircuitPython as references in writing these.

This software has been written for Python 3 on the FreeBSD operating system.
I expect it will work on other POSIX systems, and maybe even on ms-windows.
But I haven't tested that.

Wiring the BME280
-----------------

Both the BME280 and the FT232H breakout boards were placed on a small
breadboard. I connected the breakout boards via SPI to run
``bme280-monitor-spi.py``:

* 5V to VIN
* GND to GND
* D0 to SCK
* D1 to SDI
* D2 to SDO
* D3 to CS

Note that for this to work, any *native* driver for FTDI chips needs to be
unloaded and disabled. On FreeBSD the first is achieved by running ``kldunload
uftdi.ko`` as root. The second step is accomplished by commenting out the
``nomatch`` statement in ``/etc/devd/usb.conf`` that loads ``uftdi`` driver
and restarting ``devd`` by running ``service devd restart`` as root.

The module
----------

Assuming you are in the directory where the ``bme280.py`` module lives, and
you have installed ``pyftdi``, you can use it as follows. First copy the
following into an IPython 3 session or a Python 3 interpreter.

.. code-block:: python

    from time import sleep
    from pyftdi.spi import SpiController
    from bme280 import Bme280spi
    ctrl = SpiController()
    ctrl.configure('ftdi://ftdi:232h/1')  # Assuming there is only one FT232H.
    spi = ctrl.get_port(0)  # Assuming D3 is used for chip select.
    spi.set_frequency(1000000)
    bme280 = Bme280spi(spi)

Now you are ready to measure.

.. code-block:: python

    while True:
        print(bme280.read())
        sleep(5)

This should print a (temperature, pressure, relative humidity) tuple every
five seconds.

The monitoring program
----------------------

The ``bme280-monitor-spi.py`` program is designed to be started from the command
line, where it should probably be started so as to run in the background. Run
``./bme280-monitor-spi.py -h`` to see the optional and required parameters.

An example:

.. code-block:: console

    ./bme280-monitor-spi.py -i 900 /tmp/bme280-{}.d

This will write data to a file in ``/tmp`` every fifteen minutes. The data
will look like this::

    # BME280 data.
    # Started monitoring at 2018-04-28T19:38:01Z.
    # Per line, the data items are:
    # * UTC date and time in ISO8601 format
    # * Temperature in °C
    # * Pressure in Pa
    # * Relative humidity in %.
    2018-04-28T19:38:02Z 20.72 68476 78.04
    2018-04-28T19:53:02Z 20.41 100980 56.52
    2018-04-28T20:08:02Z 20.38 100992 56.93

The first measurement should be ignored since it was taken shortly after the
chip was reset.
