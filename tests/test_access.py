import unittest
from unittest.mock import Mock
import logging

from modbus_cli.access import parse_accesses, Access

logging.basicConfig(level=logging.DEBUG)


def mocked_modbus():
    modbus = Mock()
    modbus.slave_id = 42

    modbus.protocol = Mock()
    modbus.protocol.read_input_registers = Mock(return_value=[])
    modbus.protocol.read_holding_registers = Mock(return_value=[])
    modbus.protocol.read_discrete_inputs = Mock(return_value=[])
    modbus.protocol.read_coils = Mock(return_value=[])

    modbus.protocol.write_multiple_registers = Mock(return_value=[])
    modbus.protocol.write_multiple_coils = Mock(return_value=[])

    return modbus


class TestAccess(unittest.TestCase):

    def test_defaults(self):
        it = parse_accesses(['123'], None)
        self.assertEqual(1, len(it))

        it = it[0]
        self.assertEqual('h', it.modbus_type)
        self.assertEqual(123, it.address())
        self.assertEqual('!H', it.pack_type())
        self.assertEqual(None, it.presenter())
        self.assertEqual(1, it.size())

    def test_full(self):
        it = parse_accesses(['i@123/<4H:STATUS'], None)
        self.assertEqual(1, len(it))

        it = it[0]
        self.assertEqual('i', it.modbus_type)
        self.assertEqual(123, it.address())
        self.assertEqual('<4H', it.pack_type())
        self.assertEqual(':STATUS', it.presenter())
        self.assertEqual(4, it.size())

    def test_grouping(self):
        it = parse_accesses(['123', '124'], None)
        self.assertEqual(1, len(it))

        it = it[0]
        self.assertEqual('h', it.modbus_type)
        self.assertEqual(123, it.address())
        self.assertEqual('!H', it.pack_type())
        self.assertEqual(None, it.presenter())
        self.assertEqual(2, it.size())

    def test_read_input_registers(self):
        modbus = mocked_modbus()
        modbus.receive = Mock(return_value=[0x1234, 0x5678])
        access = Access('i', [123, 124], ['!H', '!H'])
        access.perform(modbus)

        modbus.protocol.read_input_registers.assert_called_once_with(42, 123, 2)
        modbus.send.assert_called_once()

        self.assertEqual([(0x1234, ), (0x5678, )], access.values)

    def test_read_holding_registers(self):
        modbus = mocked_modbus()
        modbus.receive = Mock(return_value=[0x1234, 0x5678])
        access = Access('h', [123, 124], ['!H', '!H'])
        access.perform(modbus)

        modbus.protocol.read_holding_registers.assert_called_once_with(42, 123, 2)
        modbus.send.assert_called_once()

        self.assertEqual([(0x1234, ), (0x5678, )], access.values)

    def test_read_discrete_inputs(self):
        modbus = mocked_modbus()
        modbus.receive = Mock(return_value=[1, 0])
        access = Access('d', [123, 124], ['!B', '!B'])
        access.perform(modbus)

        modbus.protocol.read_discrete_inputs.assert_called_once_with(42, 123, 2)
        modbus.send.assert_called_once()

        self.assertEqual([(1,), (0,)], access.values)

    def test_read_coils(self):
        modbus = mocked_modbus()
        modbus.receive = Mock(return_value=[1, 0])
        access = Access('c', [123, 124], ['!B', '!B'])
        access.perform(modbus)

        modbus.protocol.read_coils.assert_called_once_with(42, 123, 2)
        modbus.send.assert_called_once()

        self.assertEqual([(1,), (0,)], access.values)

    def test_write_registers(self):
        modbus = mocked_modbus()
        access = Access('h', [123, 124], ['!H', '!H'], values=['10', '11'])
        access.perform(modbus)

        modbus.protocol.write_multiple_registers.assert_called_once_with(42, 123, [10, 11])
        modbus.send.assert_called_once()

    def test_write_coils(self):
        modbus = mocked_modbus()
        access = Access('c', [123, 124], ['!B', '!B'], values=['1', '0'])
        access.perform(modbus)

        modbus.protocol.write_multiple_coils.assert_called_once_with(42, 123, [1, 0])
        modbus.send.assert_called_once()

    def test_presenter(self):
        pass

    def test_endianness_read(self):
        modbus = mocked_modbus()

        # given these two 16 bit registers, what do we interpret?
        modbus.receive = Mock(return_value=[0x1122, 0x3344])

        def perform(byte_order, fields):
            addresses = list(range(len(fields)))
            access = Access('h', addresses, fields, byte_order=byte_order)
            access.perform(modbus)
            return access.values

        # big endian 16/32 bit fields
        self.assertEqual(perform('be', ['>H', '>H']), [(0x1122, ), (0x3344, )])
        self.assertEqual(perform('be', ['>I']), [(0x11223344, )])

        # little endian 16/32 bit fields
        self.assertEqual(perform('le', ['<H', '<H']), [(0x2211, ), (0x4433, )])
        self.assertEqual(perform('le', ['<I']), [(0x44332211, )])

        # mixed endian 16/32 bit fields
        self.assertEqual(perform('mixed', ['<H', '<H']), [(0x1122, ), (0x3344, )])
        self.assertEqual(perform('mixed', ['<I']), [(0x33441122, )])

    def test_endianness_write(self):
        modbus = mocked_modbus()

        # given these user inputs, what 16 bit registers are actually committed?
        values16 = ["0x1122", "0x3344"]
        values32 = ["0x11223344"]

        def perform(byte_order, fields, values):
            addresses = list(range(len(fields)))
            access = Access('h', addresses, fields, values=values, byte_order=byte_order)
            access.perform(modbus)
            return modbus.protocol.write_multiple_registers.call_args.args[2]

        # big endian 16/32 bit fields
        self.assertEqual(perform('be', ['>H', '>H'], values16), [0x1122, 0x3344])
        self.assertEqual(perform('be', ['>I'], values32), [0x1122, 0x3344])

        # little endian 16/32 bit fields
        self.assertEqual(perform('le', ['<H', '<H'], values16), [0x2211, 0x4433])
        self.assertEqual(perform('le', ['<I'], values32), [0x4433, 0x2211])

        # mixed endian 16/32 bit fields
        self.assertEqual(perform('mixed', ['<H', '<H'], values16), [0x1122, 0x3344])
        self.assertEqual(perform('mixed', ['<I'], values32), [0x3344, 0x1122])


if __name__ == '__main__':
    unittest.main()
