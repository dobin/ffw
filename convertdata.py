import sys
import pickle
import os

filename = sys.argv[1]
filenameOut = sys.argv[2]


with open(filename, 'rb') as f:
    data = pickle.load(f)

# make an index
if "index" not in data[0]:
    n = 0
    for input in data:
        input["index"] = n
        n += 1


newData = {
    'filename': os.path.basename(filename),
    'parentFilename': None,
    'networkData': data,
    'seed': None,
    'time': None,
}

with open(filenameOut, 'w') as f:
    pickle.dump(newData, f)
