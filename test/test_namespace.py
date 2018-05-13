#!/usr/bin/env python2

import unittest


class TestLinuxNamespace(unittest.TestCase):
    def test_Namespaces(self):
        p1 = linuxNamespace1.startProcess( ['./test/mockup_simplebind.py' ] )
        #self.assertEqual(ret, 0)

        # if this is non-0 return value, it does not work
        p2 = linuxNamespace2.startProcess( ['./test/mockup_simplebind.py' ] )
        #self.assertEqual(ret, 0)

        p1.wait()
        p2.wait()




if __name__ == '__main__':
    unittest.main()
