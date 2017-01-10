#!/user/bin/env python

import unittest
from pyCloud import Server

class TestServer(unittest.TestCase):

    def startTestRun(self):
        self.server = Server(host="192.168.223.128", username="root", password="i only know it")

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()