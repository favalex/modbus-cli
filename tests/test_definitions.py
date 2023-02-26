import unittest
import logging

from modbus_cli.definitions import Definitions

logging.basicConfig(level=logging.DEBUG)


class TestDefinitions(unittest.TestCase):

    def test_parse(self):
        it = Definitions(False)
        it.parse(['tests/simple.modbus'])
        self.assertEqual({'a_register': 'i@100/4H:a_presenter'}, it.registers)
        self.assertEqual({':a_presenter': {0: 'x', 1: 'y'}}, it.presenters)

    def test_parse_silent(self):
        it = Definitions(True)
        it.parse(['tests/simple.modbus'])
        self.assertEqual({'a_register': 'i@100/4H:a_presenter'}, it.registers)
        self.assertEqual({':a_presenter': {0: 'x', 1: 'y'}}, it.presenters)


if __name__ == '__main__':
    unittest.main()
