
import os
import time
import pickle 
import logging 

import servermanager
import networkmanager


class Tester():
    def __init__(self, config):
        self.config = config

    def test(self):
        targetPort = 20000
        serverManager = servermanager.ServerManager(self.config, 0, targetPort)
        networkManager = networkmanager.NetworkManager(self.config, targetPort)

        serverManager.start()

	file = self.config["inputs"] + "/data_0.pickle"
	if not os.path.isfile(file):
            logging.error("Could not read input file: " + file)
            sys.exit(0)
        with open(file, 'rb') as f:
            self.config["_inputs"] = pickle.load(f)

        if not networkManager.openConnection():
            print "Didnt start"
            return

        stats = {}
        it = 0
        while it < 3:
            n = 0
    	    for message in self.config["_inputs"]:
                print "Handling msg: " + str(n)
	    	if message["from"] == "srv":
                    print "Receive: "
                    print "  Expect: " + str(len(message["data"]))
                    ret = networkManager.receiveData()
                    if len(message["data"]) != len(ret):
                        print "    FAIL"

                        if n in stats:
                            stats[n] += 1
                        else: 
                            stats[n] = 1

	    	if message["from"] == "cli":
            	    ret = networkManager.sendData(message["data"])
            	    if not ret:
                	logging.debug("  server not reachable")
                        if n in stats:
                            stats[n] += 1
                        else: 
                            stats[n] = 1

                n += 1
            it+=1
            networkManager.closeConnection()
            networkManager.openConnection()

        print "Itercount: " + str(it)
        for key, value in stats.iteritems():
            print "Fails at msg #" + str(key) + ": " + str(value)
