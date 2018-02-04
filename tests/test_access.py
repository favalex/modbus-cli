import unittest
import logging

from modbus_cli.access import parse_accesses

logging.basicConfig(level=logging.DEBUG)


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


if __name__ == '__main__':
    unittest.main()
