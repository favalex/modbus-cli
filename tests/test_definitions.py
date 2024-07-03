import unittest
import logging
import os

from modbus_cli.definitions import Definitions

logging.basicConfig(level=logging.DEBUG)

script_dir = os.path.dirname(os.path.realpath(__file__))


class TestDefinitions(unittest.TestCase):

    def test_parse(self):
        it = Definitions(False)
        it.parse([os.path.join(script_dir, 'simple.modbus')])
        self.assertEqual({'a_register': 'i@100/4H:a_presenter'}, it.registers)
        self.assertEqual({':a_presenter': {0: 'x', 1: 'y'}}, it.presenters)

    def test_parse_silent(self):
        it = Definitions(True)
        it.parse([os.path.join(script_dir, 'simple.modbus')])
        self.assertEqual({'a_register': 'i@100/4H:a_presenter'}, it.registers)
        self.assertEqual({':a_presenter': {0: 'x', 1: 'y'}}, it.presenters)


if __name__ == '__main__':
    unittest.main()
