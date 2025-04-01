import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-i',dest='input')
parser.add_argument('-o',dest='output')
parser.add_argument('-v',dest='verbose',default=0)
args = parser.parse_args()

if args.verbose > 0:
    print("Removing ********* in cyclone-tracks")

with open(args.input, 'r') as file:
    lines = file.readlines()

modified_lines = [line.replace('********','  999999') for line in lines]

with open(args.output,'w') as file:
    file.writelines(modified_lines)

if args.verbose > 0:
    print(f"Replacements done. Modified file saved as: {args.output}")
