import struct
from itertools import zip_longest, groupby
import logging
import re
import fnmatch

import umodbus.exceptions

from .definitions import REGISTER_RE


def grouper(iterable, n, fillvalue=None):
    'Collect data into fixed-length chunks or blocks'
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def dump(xs):
    return ' '.join('{:02x}'.format(x) for x in xs)


class Access:
    def __init__(self, modbus_type, addresses, pack_types, values=None, names=None, presenters=None):
        self.modbus_type = modbus_type
        self.values_to_write = values or [None] * len(addresses)
        self.addresses = addresses
        self.pack_types = pack_types
        self.names = names or [None] * len(addresses)
        self.presenters = presenters or [None] * len(addresses)

    def address(self):
        return self.addresses[0]

    def pack_type(self):
        return self.pack_types[0]

    def presenter(self):
        return self.presenters[0]

    def endianness(self):
        return self.pack_type()[0]

    @property
    def write(self):
        return any(x is not None for x in self.values_to_write)

    def size(self):
        """Number of registers"""
        total = 0
        for p in self.pack_types:
            size = struct.calcsize(p)
            if self.modbus_type in ('h', 'i'):
                assert size % 2 == 0
                size //= 2

            total += size

        return total

    def operations(self):
        if self.write:
            return zip(self.pack_types, self.values_to_write)
        else:
            return self.pack_types

    def append(self, other):
        self.names.extend(other.names)
        self.pack_types.extend(other.pack_types)
        self.addresses.extend(other.addresses)
        self.presenters.extend(other.presenters)
        if self.write:
            self.values_to_write.extend(other.values_to_write)

    def labels(self):
        return (name or address for (name, address) in zip(self.names, self.addresses))

    def print_values(self, definitions=None):
        for label, value, presenter in zip(self.labels(), self.values, self.presenters):
            if len(value) == 1:
                value = value[0]
            print('{}: {} {}'.format(label, value, self.present_value(value, presenter, definitions)))

    def present_value(self, value, presenter, definitions):
        if type(value) != int:
            return ''

        presentation = [hex(value)]

        if presenter:
            if presenter[0] == ':':
                presentation.append(definitions.presenters[presenter][value])
            elif presenter[0] == '|':
                names = []
                for bit, name in definitions.presenters[presenter].items():
                    if value & (1 << bit):
                        names.append(name)
                presentation.append(' | '.join(names))

        return ' '.join(presentation)

    def perform(self, modbus):
        if self.write:
            self.write_registers_send(modbus)
            self.write_registers_receive(modbus)
        else:
            self.read_registers_send(modbus)
            self.read_registers_receive(modbus)

    def read_registers_send(self, modbus):
        if self.modbus_type in 'cd':
            n_registers = 0
            for pack_type in self.pack_types:
                n_registers += struct.calcsize(pack_type)
        else:
            n_bytes = 0

            for pack_type in self.pack_types:
                n_bytes += struct.calcsize(pack_type)
                assert n_bytes % 2 == 0

            n_registers = n_bytes // 2

        reader = {
                'c': 'read_coils',
                'd': 'read_discrete_inputs',
                'h': 'read_holding_registers',
                'i': 'read_input_registers',
                }[self.modbus_type]

        self.request = getattr(modbus.protocol, reader)(modbus.slave_id, self.address(), n_registers)

        logging.debug('→ < %s >', dump(self.request))

        modbus.send(self.request)

    def read_registers_receive(self, modbus):
        try:
            words = modbus.receive(self.request)
        except umodbus.exceptions.IllegalDataAddressError:
            self.values = ('Invalid address', )
            return
        except umodbus.exceptions.IllegalFunctionError:
            self.values = ('Invalid modbus type', )
            return

        logging.debug('← %s', words)

        if self.modbus_type in 'cd':
            self.values = [(w,) for w in words]
        else:
            packed = struct.pack('>{}H'.format(len(words)), *words)

            self.values = []

            for pack in self.pack_types:
                size = struct.calcsize(pack)
                self.values.append(struct.unpack(pack, packed[:size]))
                packed = packed[size:]

    def write_registers_send(self, modbus):
        if self.modbus_type == 'c':
            if len(self.values_to_write) == 1:
                # TODO validate value, should be boolean
                message = modbus.protocol.write_single_coil(modbus.slave_id, self.address(), int(self.values_to_write[0]))
            else:
                message = modbus.protocol.write_multiple_coils(modbus.slave_id, self.address(),
                                                               [int(v) for v in self.values_to_write])
        else:
            words = []

            for pack_type, value in zip(self.pack_types, self.values_to_write):
                n_bytes = struct.calcsize(pack_type)
                assert n_bytes % 2 == 0

                if 'f' in pack_type or 'd' in pack_type:
                    value = float(value)
                else:
                    value = int(value, 0)

                words.extend([h << 8 | l for h, l in grouper(struct.pack(pack_type, value), 2)])

            if len(words) == 1:
                message = modbus.protocol.write_single_register(modbus.slave_id, self.address(), words[0])
            else:
                message = modbus.protocol.write_multiple_registers(modbus.slave_id, self.address(), words)

        logging.debug('→ < %s >', dump(message))

        self.request = message

        return modbus.send(message)

    def write_registers_receive(self, modbus):
        modbus.receive(self.request)

    def __str__(self):
        return '{}@{}/{}{}'.format(self.modbus_type,
                                   self.address(),
                                   self.pack_types,
                                   '={}'.format(self.values_to_write) if self.write else '')

    def __repr__(self):
        return 'Access({!r}, {!r}, {!r}, {!r}, {!r})'.format(self.modbus_type, self.addresses, self.pack_types, self.values_to_write, self.names)


def by_type(access):
    return access.modbus_type, access.write, access.endianness()


def by_address(access):
    return access.address()


def group_accesses(accesses):
    grouped = []

    for (modbus_type, write, _), xs in groupby(sorted(accesses, key=by_type), key=by_type):
        xs = sorted(xs, key=by_address)
        while len(xs):
            first = xs.pop(0)
            while len(xs):
                second = xs[0]
                if first.address() + first.size() == second.address():
                    first.append(second)
                    xs.pop(0)
                else:
                    break
            grouped.append(first)

    return grouped


def parse_access(register, name, write, value):
    modbus_type, address, pack_type, presenter = re.match(REGISTER_RE, register).groups()

    if not address:
        logging.warn('%r is not a known named register nor a valid register definition. Skipping it.', register)
        return None

    if not modbus_type:
        modbus_type = 'h'
    else:
        modbus_type = modbus_type[:-1]

    if not pack_type:
        if modbus_type in 'cd':
            pack_type = 'B'
        else:
            pack_type = '!H'
    else:
        pack_type = pack_type[1:]

    address = int(address)

    if pack_type[0] not in '@=<>!':
        pack_type = '!' + pack_type

    modbus_type = modbus_type.lower()
    if modbus_type not in 'cdhi':
        raise ValueError("Invalid Modbus type '{}'. Valid ones are 'cdhi'".format(modbus_type))
    if write and modbus_type not in 'ch':
        raise ValueError("Invalid Modbus type '{}'. Only coils and holding registers are writable".format(modbus_type))

    return Access(modbus_type, [address], [pack_type], [value], names=[name], presenters=[presenter])


def parse_accesses(s, definitions):
    accesses = []

    for access in s:
        parts = access.split('=')
        if len(parts) == 1:
            register = parts[0]
            value = None
            write = False
        else:
            register, value = parts
            write = True

        if re.fullmatch(REGISTER_RE, register):
            access = parse_access(register, None, write, value)
            if access:
                accesses.append(access)
        else:
            register_re = re.compile(fnmatch.translate(register))
            for name, definition in definitions.registers.items():
                if register_re.match(name):
                    access = parse_access(definition, name, write, value)
                    if access:
                        accesses.append(access)

    return group_accesses(accesses)
