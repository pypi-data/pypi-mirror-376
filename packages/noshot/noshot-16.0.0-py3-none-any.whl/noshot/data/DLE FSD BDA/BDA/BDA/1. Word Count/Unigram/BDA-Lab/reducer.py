import sys

current_word = None
current_count = 0

for line in sys.stdin:
    word, count = line.strip().split()
    count = int(count)

    if current_word == word:
        current_count += count
    else:
        if current_word:
            print '%-20s %s' % (current_word, current_count)
        current_word = word
        current_count = count

if current_word:
    print '%-20s %s' % (current_word, current_count)