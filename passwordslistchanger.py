import sys
import argparse

def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-i',
        '--inputfile',
        help='Input argument file',
        type=argparse.FileType('r', encoding='UTF-8'), 
        required=True
    )
    parser.add_argument(
        '-o',
        '--outputfile',
        help='Output argument file',
        required=True
    )
    parser.add_argument(
        '-a',
        '--attempts',
        help="Attempt amount",
        default=10,
        type=int
    )
    parser.add_argument(
        '-H',
        '--hash',
        help="Hash to crack",
        default="",
        type=str
    )

    args = parser.parse_args(arguments)
    input_lines = args.inputfile.readlines()
    args.inputfile.close()
    f = open(args.outputfile, 'w', encoding="UTF-8")
    numofnewlines = 1
    newlinelist = []
    lastlineslist = []
    for i, line in enumerate(input_lines):
        newlinelist.append(line.rstrip("\n"))
        if i%args.attempts == 0 and i!=0:
            newlinelist.insert(0, args.hash)
            newline = ' '.join(newlinelist)
            f.writelines(f'{newline}' + '\n')
            newlinelist = []
            numofnewlines = numofnewlines+1
        if i > len(input_lines)-args.attempts and i > args.attempts and i > len(input_lines)-numofnewlines*args.attempts:
            lastlineslist.append(line.rstrip("\n"))
    lastlineslist.insert(0, args.hash)
    newline = ' '.join(lastlineslist)
    f.writelines(f'{newline}' + '\n')
    f.close()
            

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))