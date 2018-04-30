
import os
import distutils.spawn
from mutator.mutatorinterface import testMutatorConfig
import defaultconfig

class ConfigManager(object):
    def _isRoot(self):
        return os.geteuid() == 0


    def checkRequirements(self, config):
        if not os.path.isfile(config["target_bin"]):
            print "Target binary not found: " + str(config["target_bin"])
            return False

        if not os.path.isdir(config["temp_dir"]):
            print "Temp directory not found: " + str(config["temp_dir"])
            return False

        if not os.path.isfile(config["target_bin"]):
            print "Target Binary not found: " + str(config["target_bin"])
            return False

        if distutils.spawn.find_executable("gdb") is None:
            print "GDB not installed?"
            return False

        return True


    def checkFuzzRequirements(self, config):
        if not testMutatorConfig(config):
            return False

        if 'use_netnamespace' in config and config['use_netnamespace']:
            if not self._isRoot():
                print('"use_namespace" active but you are not root.')
                print('This requires root')
                print('(and also nested namespaces in container)')
                return False
            else:
                print('Rember "use_netnamespace requires nesting in container"')

        return True



    def loadConfigByFile(self, configfilename, basedir):
        rawData = open(configfilename, 'r').read()
        # hmm this produces some strange behaviour upon string comparison
        # of the values of the dict
        #pyData = ast.literal_eval(rawData)
        pyData = eval(rawData)

        return self._loadConfig(pyData, basedir)


    def loadConfigByDict(self, config, basedir):
        return self._loadConfig(config, basedir)


    def _loadConfig(self, pyData, basedir):
        config = defaultconfig.DefaultConfig.copy()

        pyData["basedir"] = basedir
        pyData["projdir"] = os.getcwd() + "/"

        for key in pyData:
            config[key] = pyData[key]

        # cleanup. Damn this is ugly.
        config["target_bin"] = config["projdir"] + config["target_bin"]
        config["input_dir"] = config["projdir"] + config["input_dir"]
        config["temp_dir"] = config["projdir"] + config["temp_dir"]
        config["outcome_dir"] = config["projdir"] + config["outcome_dir"]
        config["verified_dir"] = config["projdir"] + config["verified_dir"]
        config["grammars"] = config["projdir"] + config["grammars"]

        return config


    def checkConfig(self, pyData):
        requiredConfigKeys = [
            'name',
            'target_bin',
            'target_args',
            'target_port',
            'ipproto']
        for key in requiredConfigKeys:
            if key not in pyData:
                print "Configuration directive not found: " + key
                return False

        return True
