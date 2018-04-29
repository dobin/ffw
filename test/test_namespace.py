#!/usr/bin/env python2

import unittest
from target.linuxnamespace import LinuxNamespace


class TestLinuxNamespace(unittest.TestCase):
    def test_Namespaces(self):
        # this can fail pretty quickly (non root etc)
        linuxNamespace1 = LinuxNamespace(1)
        linuxNamespace2 = LinuxNamespace(2)

        ret = linuxNamespace1.startProcess( ['./test/mockup_simplebind.py' ] )
        self.assertEqual(ret, 0)

        # if this is non-0 return value, it does not work
        ret = linuxNamespace2.startProcess( ['./test/mockup_simplebind.py' ] )
        self.assertEqual(ret, 0)

        linuxNamespace1.cleanup()
        linuxNamespace2.cleanup()


if __name__ == '__main__':
    unittest.main()
