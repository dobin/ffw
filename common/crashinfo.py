import pickle
import os


def exportFuzzResult(crashDataModel, fuzzIter, config):
    seed = fuzzIter.seed

    crashData = crashDataModel.getData()

    data = {
        "fuzzerCrashData": crashData,
        "fuzzIterData": fuzzIter.getData(),
    }

    # pickle file with everything
    with open(os.path.join(config["outcome_dir"], str(seed) + ".ffw"), "w") as f:
        pickle.dump(data, f)

    # Save a txt log
    with open(os.path.join(config["outcome_dir"], str(seed) + ".txt"), "w") as f:
        f.write("Seed: %s\n" % seed)
        f.write("Fuzzer: %s\n" % config["fuzzer"])
        f.write("Target: %s\n" % config["target_bin"])

        f.write("Time: %s\n" % data["fuzzIterData"]["time"])
        f.write("Fuzzerpos: %s\n" % crashData["fuzzerPos"])
        f.write("Signal: %d\n" % crashData["signum"])
        f.write("Exitcode: %d\n" % crashData["exitcode"])
        f.write("Reallydead: %s\n" % str(crashData["reallydead"]))
        f.write("PID: %s\n" % str(crashData["serverpid"]))
        f.write("Asanoutput: %s\n" % crashData["asanOutput"])
