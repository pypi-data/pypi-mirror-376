import sys

current_bigram = None
current_count = 0

for line in sys.stdin:
    bigram, count = line.strip().split('\t')
    count = int(count)

    if current_bigram == bigram:
        current_count += count
    else:
        if current_bigram:
            print '%-40s\t%s' % (current_bigram, current_count)
        current_bigram = bigram
        current_count = count

if current_bigram:
    print '%-40s\t%s' % (current_bigram, current_count)