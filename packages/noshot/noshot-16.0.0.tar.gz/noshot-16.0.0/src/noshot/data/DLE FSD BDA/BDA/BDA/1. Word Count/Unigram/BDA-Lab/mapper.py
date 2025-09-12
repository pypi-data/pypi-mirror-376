import sys

for line in sys.stdin:
    line = line.strip().lower()
    for p in [".", ",", "!", "?", "'", '"']:
        line = line.replace(p, "")

    words = line.split()
    for word in words:
        print '%-20s %s' % (word, 1)
