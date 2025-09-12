import sys

for line in sys.stdin:
    line = line.strip().lower()
    for p in [".", ",", "!", "?", "'", '"']:
        line = line.replace(p, "")
    words = line.split()

    for i in range(len(words) - 1):
        bigram = words[i] + " " + words[i+1]
        print '%-40s\t%s' % (bigram, 1)
