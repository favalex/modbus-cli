=========
modbus
=========

---------------------------------------------
Access Modbus devices from the command line
---------------------------------------------

:Author: favalex@gmail.com
:Date: 2017-06-04
:Copyright: MPL 2.0
:Version: 0.1
:Manual section: 1

SYNOPSIS
========

  modbus [-h] [-r REGISTERS] [-s SLAVE_ID] [-b BAUD] [-p STOP_BITS] [-v] device access [access ...]

DESCRIPTION
===========

modbus allows reading and writing registers of Modbus devices from the command line.

It can talk to both TCP and RTU (i.e. serial) devices and can encode and decode
types larger than 16 bits (e.g. floats) into Modbus 16 bits registers.

Register definitions (consisting of a register address and its type) can be
provided directly on the command line or loaded from a file and referred by
symbolic name, for convenience.

modbus is implemented in python on top of the protocol implementation provided
by the umodbus python library.

OPTIONS
=======

device
  ``/dev/ttyXXX`` for serial devices, or ``hostname[:port]`` for TCP devices

access
  One or more read or write operations. See ACCESS SYNTAX below.

-r FILE, --registers=FILE    Read registers definitions from FILE.
-v, --verbose                Print on screen the bytes transferred on the wire.
-b BAUD, --baud=BAUD         Set the baud rate for serial connections.
-p BITS, --stop-bits=BITS    Set the number of stop bits for serial connections.
-h, --help                   Show this help message and exit.

ACCESS SYNTAX
=============

[MODBUS_TYPE@]ADDRESS[/BINARY_TYPE][=VALUE]

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

EXAMPLES
========

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

REGISTERS FILE SYNTAX
=====================

A ``#`` starts a comment.

Each line contains a symbolic name followed by the register definition, separated by spaces.

SEE ALSO
========

* `modbus <https://en.wikipedia.org/wiki/Modbus>`__
* `umodbus <https://pypi.python.org/pypi/uModbus>`__
* `pack format <https://docs.python.org/3/library/struct.html#format-characters>`__
