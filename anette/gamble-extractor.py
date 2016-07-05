
import re
import os

p = re.compile('\d\d:\d\d:\d\d<.(\w+)>')
outputfile = "gamblefile"
nicks = set()

files = ["itstud.log", "it.log"]

for fname in files:
    print("Parsing file: " + fname)
    try:
        if os.path.isfile(fname):
            file = open(fname, 'r')
            for l in file:
               m = re.search(p, l)
               if m:
                   nicks.add(m.group(1))
    except Exception as e:
        print("Failed " + str(e))


output = open(outputfile, 'w')

for n in nicks:
    output.write(n + "\n")
