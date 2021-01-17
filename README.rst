=========
modbus
=========

---------------------------------------------
Access Modbus devices from the command line
---------------------------------------------

:Author: favalex@gmail.com
:Date: 2020-01-17
:Copyright: MPL 2.0
:Version: 0.1.5
:Manual section: 1

.. image:: https://travis-ci.org/favalex/modbus-cli.svg?branch=master
    :target: https://travis-ci.org/favalex/modbus-cli

SYNOPSIS
========

  modbus [-h] [-r REGISTERS] [-s SLAVE_ID] [-b BAUD] [-p STOP_BITS] [-P {e,o,n}] [-v] device access [access ...]

DESCRIPTION
===========

Read and write registers of Modbus devices.

Access both TCP and RTU (i.e. serial) devices and encode and decode types
larger than 16 bits (e.g. floats) into Modbus 16 bits registers.

Optionally access registers by symbolic names, as defined in a registers file.
Symbolic names for enumerations and bitfields are supported too.

Designed to work nicely with other standard UNIX tools (``watch``, ``socat``,
etc.), see the examples.

Implemented in python on top of the protocol implementation provided by the
umodbus python library.

INSTALL
=======

Regular python install, either ``pip install modbus_cli`` to install from pypi
or ``python setup.py install`` to install from source.

OPTIONS
=======

device
  ``/dev/ttyXXX`` for serial devices, or ``hostname[:port]`` for TCP devices

access
  One or more read or write operations. See ACCESS SYNTAX below.

-r FILE, --registers=FILE    Read registers definitions from FILE. Can be specified multiple times.
-v, --verbose                Print on screen the bytes transferred on the wire.
-b BAUD, --baud=BAUD         Set the baud rate for serial connections.
-p BITS, --stop-bits=BITS    Set the number of stop bits for serial connections.
-P PARITY, --parity=PARITY   Set the parity for serial connections: (e)ven, (o)dd or (n)one
-h, --help                   Show this help message and exit.

ACCESS SYNTAX
=============

::

  [MODBUS_TYPE@]ADDRESS[/BINARY_TYPE][:ENUMERATION_NAME][=VALUE]

Mnemonic: access the register(s) of MODBUS_TYPE starting *at* ADDRESS,
interpreting them as BINARY_TYPE. The ``/`` syntax is inspired by gdb (but the
available types are different.)

MODBUS_TYPE = h|i|c|d
  The modbus type, one of

  ===== ================ ======= =========
  code  name             size    writable
  ===== ================ ======= =========
  ``h`` holding register 16 bits yes
  ``i`` input register   16 bits no
  ``c`` coil             1 bit   yes
  ``d`` discrete input   1 bit   no
  ===== ================ ======= =========

The default modbus type is holding register.

ADDRESS = <number>
  0-based register address

BINARY_TYPE = <pack format>
  Any format description accepted by the python standard ``pack`` module. Some common formats are:

  ===== ====
  code  type
  ===== ====
  ``h`` 16 bits signed integer
  ``H`` 16 bits unsigned integer
  ``i`` 32 bits signed integer
  ``I`` 32 bits unsigned integer
  ``f`` 32 bits IEEE 754 float
  ===== ====

  The default byte order is big-endian, use a ``<`` prefix in the format to specify little-endian.

VALUE = <number>
  The value to be written to the register. If not present, the register will be read instead.

  If only one register is written to, the modbus function ``6 (0x6)``, "write single register" is used. 
  If multiple registers are written to, the modbus function ``16 (0x10)``, "write multiple registers" is used.

EXAMPLES
========

Read a holding register
-----------------------

::

  $ modbus $IP_OF_MODBUS_DEVICE 100

Write a holding register
------------------------

::

  $ modbus $IP_OF_MODBUS_DEVICE 100=42

Read multiple registers
-----------------------

To read (or write) multiple registers simply list them on the command line::

  $ modbus $IP_OF_MODBUS_DEVICE 100 c@2000

When performing access to multiple contiguous registers, one single modbus operation is performed.

When multiple modbus operations are needed, they are all initiated at once, and
the results are collected as they arrive.

More examples of the access syntax
----------------------------------

==================== ====
``h@39/I``           read the 32-bits unsigned integer stored in holding registers at addresses 39 and 40
``39/I``             same as above (h is the default modbus type)
``39/I=42``          write the integer 42 to that register
``SOME_REGISTER=42`` same as above, provided the registers file contains the definition ``SOME_REGISTER h@39/I``
``39/I=0xcafe``      the value can be specified in hexadecimal
``c@5``              read coil at address 5
``h@24/f=6.78``      write a floating point value to holding registers at addresses 24 and 25
``i@1/6B``           read six unsigned bytes stored in input registers at addresses 1, 2 and 3
==================== ====

Monitor a register
------------------

The UNIX command ``watch`` can be used to read a register at regular intervals::

  $ watch modbus $IP_OF_MODBUS_DEVICE 100

Read a serial device attached to a remote computer
--------------------------------------------------

The UNIX command ``socat`` can be used to access a remote device through a TCP
tunnel::

  remote$ socat -d -d tcp-l:54321,reuseaddr file:/dev/ttyUSB0,raw,b19200
  local$ socat -d -d tcp:sc:54321 pty,waitslave,link=/tmp/local_device,unlink-close=0
  local$ modbus /tmp/local_device 100

Read multiple registers based on their names
--------------------------------------------

Given the following registers definitions::

  $ cat registers.modbus
  di0 d@0
  di1 d@1
  ai0 i@512
  ai1 i@513

glob matching (\*, ?, etc.) can be used to read all the ``ai`` registers at once::

  $ modbus -r registers.modbus $IP_OF_MODBUS_DEVICE ai\*

REGISTERS FILES
=====================

The purpose of the registers files is to be able to refer to registers by name.

There can be multiple definition files, specified using either the ``-r``
command line switch or the ``MODBUS_DEFINITIONS`` environment variable.

A ``#`` in a definition file starts a comment.

Each line contains a symbolic name followed by a register definition. The name
and the definitions are separated by spaces, for example::

  status i@512:STATUS
  leds 513:LEDS

The file can also contain the possible values for an enumeration or a bitmask,
for example::

  # This is an enumeration named STATUS
  :STATUS
    0=OFF
    1=ON
    2=ERROR

  # This is a bitmask named LEDS
  |LEDS
    0=LED0
    1=LED1
    3=LED3
    4=LED4

ENVIRONMENT
===========

MODBUS_DEFINITIONS
  A colon separated list of register definitions files.

SEE ALSO
========

* `modbus <https://en.wikipedia.org/wiki/Modbus>`__
* `umodbus <https://pypi.python.org/pypi/uModbus>`__
* `pack format <https://docs.python.org/3/library/struct.html#format-characters>`__
