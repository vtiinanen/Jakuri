import sys
import time
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

    args = parser.parse_args(arguments)
    input_lines = args.inputfile.readlines()
    args.inputfile.close()

    f = open(args.outputfile, 'w')
    i = 0
    newlinelist = []
    for line in input_lines:
        line.rstrip("\n")
        newlinelist.append(line)
        if i%10 == 0 and i!=0:
            newlinelist.insert(0, '87e93406a19d11166fd4aff9addf299aad2221cbd45febc596a527b65269b78f')
            print(newlinelist)
            newline = ','.join(newlinelist)
            f.writelines(f'{newline}' + '\n')
            newlinelist = []
        i = i+1
    f.close()
            

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))