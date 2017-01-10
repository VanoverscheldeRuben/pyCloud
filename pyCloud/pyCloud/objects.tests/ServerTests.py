#!/usr/bin/env python

import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import unittest
from objects.Server import Server

class TestServer(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.server = Server(host="192.168.223.128", port="22", username="user", password="password")
        self.serverWithoutHost = Server(port="22", username="user", password="password")
        self.serverWithoutPort = Server(host="192.168.223.128", username="user", password="password")
        self.serverWithoutUsername = Server(host="192.168.223.128", port="22", password="password")
        self.serverWithoutPassword = Server(host="192.168.223.128", port="22", username="user")

    def test_constructorFullyInitialized(self):
        self.assertEqual(self.server.getHost(), "192.168.223.128")
        self.assertEqual(self.server.getPort(), "22")
        self.assertEqual(self.server.getUsername(), "user")
        self.assertEqual(self.server.getPassword(), "password")

    def test_constructorWithoutHost(self):
        self.assertEqual(self.serverWithoutHost.getHost(), "127.0.0.1")
        self.assertEqual(self.serverWithoutHost.getPort(), "22")
        self.assertEqual(self.serverWithoutHost.getUsername(), "user")
        self.assertEqual(self.serverWithoutHost.getPassword(), "password")

    def test_constructorWithoutPort(self):
        self.assertEqual(self.serverWithoutPort.getHost(), "192.168.223.128")
        self.assertEqual(self.serverWithoutPort.getPort(), None)
        self.assertEqual(self.serverWithoutPort.getUsername(), "user")
        self.assertEqual(self.serverWithoutPort.getPassword(), "password")

    def test_constructorWithoutUsername(self):
        self.assertEqual(self.serverWithoutUsername.getHost(), "192.168.223.128")
        self.assertEqual(self.serverWithoutUsername.getPort(), "22")
        self.assertEqual(self.serverWithoutUsername.getUsername(), None)
        self.assertEqual(self.serverWithoutUsername.getPassword(), "password")

    def test_constructorWithoutPassword(self):
        self.assertEqual(self.serverWithoutPassword.getHost(), "192.168.223.128")
        self.assertEqual(self.serverWithoutPassword.getPort(), "22")
        self.assertEqual(self.serverWithoutPassword.getUsername(), "user")
        self.assertEqual(self.serverWithoutPassword.getPassword(), None)

if __name__ == '__main__':
    unittest.main()