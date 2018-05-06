import os

directory = "./"

res = {}

for filename in os.listdir(directory):
    time = os.path.getmtime(directory + filename)
    time = int(time)
    print filename + ": " + str(time)
    res[time] = filename

minimum = None
for key in sorted(res):
    if minimum is None:
        minimum = key

    t = key - minimum
    print str(t) + ": " + res[key]


