#!/usr/bin/env python

'''Post a message to twitter'''

from __future__ import print_function

try:
    import configparser
except ImportError as _:
    import ConfigParser as configparser

import getopt
import os
import sys
import twitter

"""
$ cat tweet.conf
[Tweet]
consumer_key:
consumer_secret:
access_key:
access_secret:
"""

class TweetRc(object):
    def __init__(self, configpath):
        self.configpath = configpath
        self._config = None

    def GetConsumerKey(self):
        return self._GetOption('consumer_key')

    def GetConsumerSecret(self):
        return self._GetOption('consumer_secret')

    def GetAccessKey(self):
        return self._GetOption('access_key')

    def GetAccessSecret(self):
        return self._GetOption('access_secret')

    def _GetOption(self, option):
        try:
            return self._GetConfig().get('Tweet', option)
        except:
            return None

    def _GetConfig(self):
        if not self._config:
            self._config = configparser.ConfigParser()
            self._config.read(os.path.expanduser(self.configpath))
        return self._config


class TwitterInterface():
    def __init__(self, config):
        self.api = None
        self.config = config


    def load(self):
        filelocation = os.path.join(self.config['basedir'], "tweet.conf")
        rc = TweetRc(filelocation)
        consumer_key = rc.GetConsumerKey()
        consumer_secret = rc.GetConsumerSecret()
        access_key = rc.GetAccessKey()
        access_secret = rc.GetAccessSecret()
        encoding = None
        if not consumer_key or not consumer_secret or not access_key or not access_secret:
            raise Exception("Could not load twitter config in: " + filelocation)

        self.api = twitter.Api(consumer_key=consumer_key, consumer_secret=consumer_secret,
                          access_token_key=access_key, access_token_secret=access_secret,
                          input_encoding=encoding)


    def tweet(self, message):
        status = self.api.PostUpdate(message)


def testTwitterInterface():
    fuzzTwitter = FuzzTwitter()
    fuzzTwitter.load()
    fuzzTwitter.tweet("Test")


if __name__ == "__main__":
    testTwitterInterface()
