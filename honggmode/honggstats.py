import time
import sys
import logging


from honggslave import HonggSlave


class HonggStats(object):
    def __init__(self, numThreads):
        self.perf = {}
        self.stats = {
            'iterCount': 0,  # execs_done
            'corpusCount': 0,  # paths_total
            'crashCount': 0,  # unique_crashes
            'hangCount': 0,  # unique_hangs
            'fps': 0,  # execs_per_sec

            'start_time': self.getUnixTime(),
            'last_update': 0,
            'max_depth': 0,
            'last_path': 0,
            'last_crash': 0,
            'last_hang': 0,
            'execs_since_crash': 0,

            'latency': 0,
            'timeouts': 0,
        }

        n = 0
        while n < numThreads:
            self.perf[n] = HonggSlave.createHonggSlaveMasterData(n, 0, 0, 0, 0, 0, 0, 0, 0)
            n += 1


    def getUnixTime(self):
        return int(time.time())


    def start(self):
        self.f = open("plot_data", "w+")
        header = "unix_time, cycles_done, cur_path, paths_total, pending_total, "
        header += "pending_favs, map_size, unique_crashes, unique_hangs, max_depth, "
        header += "execs_per_sec\n"
        self.f.write(header)


    def finish(self):
        self.f.close()


    def sanityChecks(self):
        for perf in self.perf:
            if self.perf[perf]['maxLatency'] > 0.1:
                logging.warn("Latency > 0.1! Decrease amount of processes!")

        if self.stats['corpusCount'] < 5:
            logging.warn("No new basic blocks found!")
            logging.warn("Are you sure you compiled target with honggfuzz?")

        if self.stats['timeouts'] > ( self.stats['iterCount'] / 10 ):
            logging.warn(">10 percent Timeout count (%d iterations, %d timeouts)"
                         % ( self.stats['timeouts'], self.stats['iterCount']) )
            logging.warn("Fuzzing is not effective. Identify reason of connection")
            logging.warn("Timeout, use --test, and restart.")


    def writePlotData(self):
        # unix_time, cycles_done, cur_path, paths_total, pending_total,
        # pending_favs, map_size, unique_crashes, unique_hangs, max_depth,
        # execs_per_sec
        self.f.write(str(int(time.time())) + ', ')  # unixtime
        #self.f.write(str(self.stats['iterCount']) + ', ')  # cycles_done
        self.f.write('0' + ', ')  # cycles_done
        self.f.write('0' + ', ')  # cur_path
        self.f.write(str(self.stats['corpusCount']) + ', ')  # paths_total
        self.f.write('0' + ', ')  # pending_total
        self.f.write('0' + ', ')  # pending_favs
        self.f.write('0' + ', ')  # map_size
        self.f.write(str(self.stats['crashCount']) + ', ')  # unique_crashes
        self.f.write(str(self.stats['hangCount']) + ', ')  # unique_hangs
        self.f.write('0' + ', ')  # max_depth
        self.f.write(str(self.stats['fps']) + '\n')  # execs_per_sec
        self.f.flush()


    def addToStats(self, r):
        # get previous stats of the thread
        prev_r = self.perf[ r['threadId'] ]
        self.stats['last_update'] = self.getUnixTime()

        cnt = r['iterCount'] - prev_r['iterCount']
        self.stats['iterCount'] += cnt

        cnt = r['corpusCount'] - prev_r['corpusCount']
        self.stats['corpusCount'] += cnt
        if cnt > 0:
            self.stats['last_path'] = self.getUnixTime()

        cnt = r['crashCount'] - prev_r['crashCount']
        self.stats['crashCount'] += cnt
        if cnt > 0:
            self.stats['last_crash'] = self.getUnixTime()

        cnt = r['hangCount'] - prev_r['hangCount']
        self.stats['hangCount'] += cnt
        if cnt > 0:
            self.stats['last_hang'] = self.getUnixTime()

        cnt = r['fuzzPerSec'] - prev_r['fuzzPerSec']
        self.stats['fps'] += cnt

        self.stats['latency'] = (self.stats['latency'] + r['maxLatency']) / 2

        cnt = r['timeoutCount'] - prev_r['timeoutCount']
        self.stats['timeouts'] += cnt

        # set the stats to the current one
        self.perf[ r['threadId'] ] = r


    def printSomeStats(self):
        for perf in self.perf:
            p = self.perf[perf]
            r = (
                p['threadId'],
                p['iterCount'],
                p['corpusCount'],
                p['corpusCountOverall'],
                p['crashCount'],
                p['hangCount'],
                p['fuzzPerSec'],
                p['maxLatency'],
                p['timeoutCount']
            )
            print("%3d  It: %4d  CorpusNew: %2d  CorpusOerall %2d  Crashes: %2d  HangCount: %2d  Fuzz/s: %2.1f  Latency: %.4f  Timeouts: %3d" % r)


    def printAflStats(self):
        # unix_time, cycles_done, cur_path, paths_total, pending_total,
        # pending_favs, map_size, unique_crashes, unique_hangs, max_depth,
        # execs_per_sec
        sys.stdout.write(str(int(time.time())) + ', ')  # unixtime
        sys.stdout.write('0' + ', ')  # cycles_done
        sys.stdout.write('0' + ', ')  # cur_path
        sys.stdout.write(str(self.stats['corpusCount']) + ', ')  # paths_total
        sys.stdout.write('0' + ', ')  # pending_total
        sys.stdout.write('0' + ', ')  # pending_favs
        sys.stdout.write('0' + ', ')  # map_size
        sys.stdout.write(str(self.stats['crashCount']) + ', ')  # unique_crashes
        sys.stdout.write(str(self.stats['hangCount']) + ', ')  # unique_hangs
        sys.stdout.write('0' + ', ')  # max_depth
        sys.stdout.write(str(self.stats['fps']) + '\n')  # execs_per_sec


    def writeFuzzerStats(self):
        """
        start_time        : 1523018783
        last_update       : 1523020186
        fuzzer_pid        : 130808
        cycles_done       : 0
        execs_done        : 1554451
        execs_per_sec     : 1023.57
        paths_total       : 458
        paths_favored     : 154
        paths_found       : 452
        paths_imported    : 0
        max_depth         : 3
        cur_path          : 25
        pending_favs      : 151
        pending_total     : 452
        variable_paths    : 52
        stability         : 99.90%
        bitmap_cvg        : 4.79%
        unique_crashes    : 13
        unique_hangs      : 21
        last_path         : 1523020107
        last_crash        : 1523019341
        last_hang         : 1523019336
        execs_since_crash : 1283575
        exec_timeout      : 40
        afl_banner        : lt-flac
        afl_version       : 2.52b
        target_mode       : default
        command_line      : afl-fuzz -i in -o out -- ./src/flac/.libs/lt-flac -f @@
        """
        fuzzer_stats = open("fuzzer_stats", "w+")
        fuzzer_stats.write('%-18s: %i\n' % ('start_time', self.stats['start_time']))
        fuzzer_stats.write('%-18s: %i\n' % ('last_update', self.stats['last_update']))
        fuzzer_stats.write('%-18s: %i\n' % ('fuzzer_pid', 0))
        fuzzer_stats.write('%-18s: %i\n' % ('cycles_done', 0))
        fuzzer_stats.write('%-18s: %i\n' % ('execs_done', self.stats['iterCount']))
        fuzzer_stats.write('%-18s: %i\n' % ('execs_per_second', self.stats['fps']))
        fuzzer_stats.write('%-18s: %i\n' % ('paths_total', self.stats['corpusCount']))
        fuzzer_stats.write('%-18s: %i\n' % ('paths_favored', 0))
        fuzzer_stats.write('%-18s: %i\n' % ('paths_found', 0))
        fuzzer_stats.write('%-18s: %i\n' % ('paths_imported', 0))
        fuzzer_stats.write('%-18s: %i\n' % ('max_depth', 0))
        fuzzer_stats.write('%-18s: %i\n' % ('cur_path', 0))
        fuzzer_stats.write('%-18s: %i\n' % ('pending_favs', 0))
        fuzzer_stats.write('%-18s: %i\n' % ('pending_total', 0))
        fuzzer_stats.write('%-18s: %i\n' % ('variable_paths', 0))
        fuzzer_stats.write('%-18s: %i\n' % ('stability', 0))
        fuzzer_stats.write('%-18s: %i\n' % ('bitmap_cvg', 0))
        fuzzer_stats.write('%-18s: %i\n' % ('unique_crashes', self.stats['crashCount']))
        fuzzer_stats.write('%-18s: %i\n' % ('unique_hangs', self.stats['hangCount']))
        fuzzer_stats.write('%-18s: %i\n' % ('last_path', self.stats['last_path']))
        fuzzer_stats.write('%-18s: %i\n' % ('last_crash', self.stats['last_crash']))
        fuzzer_stats.write('%-18s: %i\n' % ('last_hang', self.stats['last_hang']))
        fuzzer_stats.write('%-18s: %i\n' % ('execs_since_crash', 0))
        fuzzer_stats.write('%-18s: %i\n' % ('exec_timeout', 0))
        fuzzer_stats.write('%-18s: %s\n' % ('afl_banner', "banner"))
        fuzzer_stats.write('%-18s: %s\n' % ('afl_version', "version"))
        fuzzer_stats.write('%-18s: %s\n' % ('target_mode', "mode"))
        fuzzer_stats.write('%-18s: %s\n' % ('command_line', "cmd"))
        fuzzer_stats.close()
