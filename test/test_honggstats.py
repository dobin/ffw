#!/usr/bin/env python

import unittest

from honggmode.honggstats import HonggStats


class HonggstatsTest(unittest.TestCase):
    def test_honggstats(self):
        numThreads = 2
        honggStats = HonggStats(numThreads)

        stats1 = (0, 10, 2, 1, 2, 2, 33)
        stats2 = (1, 10, 2, 0, 1, 1, 22)

        honggStats.addToStats(stats1)
        honggStats.addToStats(stats2)

        self.assertTrue(
            honggStats.stats['iterCount'],
            20
        )
        self.assertTrue(
            honggStats.stats['corpusCount'],
            4
        )
        self.assertTrue(
            honggStats.stats['fps'],
            55
        )


if __name__ == '__main__':
    unittest.main()
