from collections import Counter
import re, sys


def clean_indels(base_string):
    # Function to replace -|+N<seq> with empty string
    def replace_indel(match):
        # Extract the number N from the match (e.g., '1' from '-1G')
        n = int(match.group(1))
        # Ensure the sequence length matches N
        seq = match.group(2)
        if len(seq) == n:
            return ''  # Remove the entire -|+N<seq> (N characters after -N)
        elif len(seq) > n:
            return seq[n:]
        else:
            sys.exit(f"bases: {base_string}, {n}{seq}")

    # Match -|+N followed by any characters, capturing N and the sequence
    cleaned = re.sub(r'[-+](\d+)([ACGTNacgtn]+)', replace_indel, base_string)
    return cleaned

def parse_pileup_line(line):
    chrom, pos, ref, depth, bases, _ = line.strip().split('\t')
    ref = ref.upper()
    counts = Counter()
    if re.search(r'[-+][0-9]+[ACGTNacgtn]+', bases):
        bases = clean_indels(bases)
    bases = re.sub(r'\^.', '', bases)
    bases = re.sub(r'\$', '', bases)
    for base in bases:
        if base in '.,': # same as ref
            counts[ref] += 1
        elif base.upper() in 'ACGT': # mismatch to ref
            counts[base.upper()] += 1
        elif base in '*#': # deletion from ref
            counts['-'] += 1

    total = sum(counts.values())
    depth = int(depth)
    if depth > 0:
        if total == depth:
            freq = {base: round(count / total, 3) for base, count in counts.items()}
            return chrom, pos, total, freq
        else:
            sys.exit(f"line: {line}, depth: {depth}, total: {total}")
    else:
        return chrom, pos, depth, {}
'''
maxpos = 0
ref = ""
with open("read_depth.txt", "r") as rf:
    last_line = rf.readlines()[-1]
    ref = last_line.split("\t")[0]
    maxpos = int(last_line.split("\t")[1])
'''    
# Read and process the pileup file
#posline = {}
with open("pileup_all_filtered.txt", "r") as f, open("base_frequency.txt", "w") as bf:
    for line in f:
        chrom, pos, total, freq = parse_pileup_line(line)
        if total > 0:
            freq_str = " ".join(f"{base}:{freq[base]}" for base in sorted(freq))
            bf.write(f"{chrom}\t{pos}\t{total}\t{freq_str}\n")
        else:
            bf.write(f"{chrom}\t{pos}\t0\n")
        #pos = int(pos)
        #posline[pos] = f"{chrom}\t{pos}\t{total}\t{freq_str}\n"
        #print(posline)
        #exit()
'''
with open("base_frequency.txt", "w") as bf:
    for i in range(maxpos):
        pos = i + 1
        if pos in posline:
            bf.write(posline[pos])
        else:
            bf.write(f"{ref}\t{pos}\t0\n")
'''