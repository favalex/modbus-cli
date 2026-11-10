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



    def test_parse_malformed_presenter_entry_skipped(self):
        import tempfile
        with tempfile.NamedTemporaryFile('w', suffix='.modbus', delete=False) as f:
            f.write('temp i@100/2H:temp_state\n')
            f.write(':temp_state 0=OFF broken-token notanint=ZZZ\n')
            path = f.name
        try:
            it = Definitions(True)
            it.parse([path])
        finally:
            os.unlink(path)
        self.assertEqual({':temp_state': {0: 'OFF'}}, it.presenters)

if __name__ == '__main__':
    unittest.main()
