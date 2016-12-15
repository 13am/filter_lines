#!/usr/bin/python

from optparse import OptionParser
import sys
import operator
import os


def parse_options():

    userinfo = '''

    FILTER LINES

    Examples:

    A. Filter the file "f1.txt" by keeping all lines which contain any of
    the words listed in the file "words.txt". Assume the file to be filtered
    contains data in columns separated by spaces. Only use the values in the
    first column of "f1.txt" to look for matches.

    > filter_lines.py --in f1.txt --keep words.txt --sep space --column 1 --out filtered_f1.txt

    B. Filter a file by values in colums. Assume the columns are named on the
    first (header) line of the input file. Output the header line and lines
    where either the "weight" column has a value greater than 13, or the value
    of the "taste" column is "good", or both.

    > filter_lines.py --in f1.txt --filters "weight>13,taste=good" --sep space --column 1 --out filtered_f1.txt

    C. As above but now keep only lines where the "weight" column has a value
    greater than 13 and the value of the "taste" column is "good".

    > filter_lines.py  --match-all --in f1.txt --filters "weight>13,taste=good" --sep space --column 1 --out filtered_f1.txt

    '''

    parser = OptionParser(usage=userinfo)

    parser.add_option('--in', type='string',
                      action='store', dest='infilename', default=False,
                      help='The file to filter. If not specified, input \
                      is read from STDIN')

    parser.add_option('--out', type='string',
                      action='store', dest='outfilename', default=False,
                      help='Name for the file where the target lines are written. \
                      If not specified, output is written to STDOUT')

    parser.add_option('--keep', type='string',
                      action='store', dest='keep', default=False,
                      help='Keep lines containing a value listed in this file.')

    parser.add_option('--remove', type='string',
                      action='store', dest='remove', default=False,
                      help='Remove lines containing a value listed in this file.')

    parser.add_option('--column',
                      action='store', dest='column',
                      help='Specify the column to be searched for the values when using'
                      ' --keep or --remove.'
                      ' The leftmost is column 1 etc.'
                      ' Multiple columns can be given by separating the column indexes'
                      ' with a comma,'
                      ' e.g. --column 1,2,5 would only search in the first,'
                      ' second, and fifth columns and'
                      ' ignore matches elsewhere.')

    parser.add_option('--match-all',
                      action='store_true', dest='match_all', default=False,
                      help='If multiple fields specified with --column or --filters,'
                      ' require that all columns  produce a match'
                      ' in order for the line itself to be counted as a match (i.e. use logical AND to join the conditions).'
                      ' Otherwise by default a match with any condition is sufficient to produce a match (a logical OR is used).')

    parser.add_option('--filter-columns',
                      action='store_true', dest='by_col', default=False,
                      help='Filter by column names (instead of values on rows) when using'
                      ' --keep or --remove.')

    parser.add_option('--excluded-out', type='string',
                      action='store', dest='outfilename_ex', default=False,
                      help='Name for the file where the excluded lines are written.'
                      ' If not specified, they are discarded.')

    parser.add_option('--header', action='store_true', dest='header', default=False,
                      help='If specified, do not filter the first line of the file.')

    parser.add_option('--sep', type='string',
                      action='store', dest='sep', default='tab',
                      help='Use this as field separator.'
                      ' The default value is tab.'
                      ' Possible values are "tab", "space", "whitespace", or any string'
                      ' such as "this script is awesome" or ";" enclosed in quotes.'
                      ' If you use the'
                      ' "whitespace" keyword as the separator, continuous stretches of'
                      ' any whitespace'
                      ' characters will be used as field separators in the input and'
                      ' the output will be'
                      ' separated by single spaces.')

    parser.add_option('--filters',
                      dest='filters',
                      action='store',
                      default=False,
                      help='Filter input lines by values in named columns.'
                      ' E.g. --filters "chrom=1,pos>3,pos<500,chrom!=MT".'
                      ' Recognizes the operators ">", "<", "=", and "!=".')

    parser.add_option('--ignore-case',
                      dest='ignore_case',
                      action='store_true',
                      default=False,
                      help='When using --keep or --remove: ignore case when '
                      'comparing letters, e.g. match "cat" to "CAT"')

    parser.add_option('--debug',
                      dest='debug',
                      action='store_true',
                      default=False,
                      help='Turn debugging reports on')

    parser.add_option('--partial-match',
                      dest='partial_match',
                      action='store_true',
                      default=False,
                      help='When using --filters: allow partial matches to column names'
                      ' (if they are unique)')

    parser.add_option('--substring-match',
                      dest='substring_match',
                      action='store_true',
                      default=False,
                      help='When using --keep or --remove: match if one and only one of the keywords'
                      ' is a substring of the target.')

    parser.add_option('--range',
                      dest='range',
                      action='store_true',
                      default=False,
                      help='--keep or --remove files contain genomic ranges'
                      ' in the tabix format. E.g. "1:400-50000", or "1".')

    parser.add_option('--chr-index',
                      dest='chr_index',
                      action='store',
                      type='int',
                      default=-666,
                      help='Index for the chromosome column. Used when'
                      ' specifying --range.')

    parser.add_option('--pos-index',
                      dest='pos_index',
                      action='store',
                      type='int',
                      default=-666,
                      help='Index for the base pair position column.'
                      ' Used when specifying --range.')

    parser.add_option('--assume-chr',
                      dest='assume_chr',
                      action='store',
                      default=False,
                      help='Use this as the chromosome code in the input.'
                      ' Used when specifying --range.')

    (options, args) = parser.parse_args()

    if not (options.keep or options.remove or options.filters):
        print_error('Please specify either --keep, --remove, or --filters')
        sys.exit(0)

    return options


def print_error(msg, vals=[]):
    m = 'Error: ' + msg.format(*vals).strip() + '\n'
    sys.stderr.write(m)


def print_debug(msg, vals=[]):
    m = 'Debug: ' + msg.format(*vals).strip() + '\n'
    sys.stderr.write(m)


def get_targets(options):
    filename = options.keep
    if filename is False:
        filename = options.remove
    try:
        input = open(filename, 'r')
    except IOError:
        print_error('The file {} was not found.', vals=(filename))
        sys.exit(0)
    targets = {}
    if options.range:
        for line in input:
            if ':' in line:
                chrom = line.split(':')[0]
                start = int(line.split(':')[1].split('-')[0])
                end = int(line.split(':')[1].split('-')[1])
            else:
                chrom = line.strip()
                start = None
                end = None
            assert start <= end
            try:
                targets[chrom].append((start, end))
            except KeyError:
                targets[chrom] = [(start, end)]
        for chrom in targets:
            targets[chrom].sort(key=lambda x: x[0])  # sort by start position
    else:
        for line in input:
            line = line.strip()
            if options.ignore_case:
                line = line.lower()
            targets[line] = 0
    input.close()

    return targets


def get_indexes(header_line, keys, options):
    indexes = {}
    header = split_line(header_line, options)

    for i in enumerate(header):
        for k in keys:
            if options.partial_match:
                match = k in i[1]
            else:
                match = k == i[1]
            if match:
                try:
                    indexes[k].append(i[0])
                except KeyError:
                    indexes[k] = [i[0]]

    unique_indexes = {}
    for k, i in indexes.items():
        u = set(i)
        if len(u) > 1:
            print_error('{} unequal matches for filter "{}"', vals=[len(u), k])
            sys.exit(0)
        else:
            unique_indexes[k] = list(u)[0]

    return unique_indexes


def float_or_return(i):
    try:
        return float(i)
    except ValueError:
        return i


class Filters:
    operators = {'!=': operator.ne,
                 '=': operator.eq,
                 '<': operator.lt,
                 '>': operator.gt}

    formatters = {'!=': float_or_return,
                  '=': float_or_return,
                  '<': float,
                  '>': float}


def build_filters(filters):
    raw_filters = filters.split(',')

    ready_filters = {}
    for f in Filters.operators.keys():
        ready_filters[f] = {}

    for f in ready_filters.keys():
        for r in raw_filters:
            if f == '=' and '!=' in r:
                continue
            if f in r:
                filter_key = r.split(f)[0]
                filter_value = r.split(f)[1]
                try:
                    ready_filters[f][filter_key].append(filter_value)
                except KeyError:
                    ready_filters[f][filter_key] = [filter_value]

    for f, targets in ready_filters.items():
        for k, v in targets.items():
            sys.stderr.write('# filter: {} {} {}\n'.format(k, f, v))

    return ready_filters


def match_by_filters(targets, line, options):
    ln = split_line(line, options)
    found_set = set()

    # options.filters: dict of dicts
    # e.g. {filter_operator:{line_index:[target_values]}}
    for filter in iter(options.filters):
        fmter = Filters.formatters[filter]
        oprtor = Filters.operators[filter]
        cols = options.filters[filter].items()
        for i, vals in cols:
            i = ln[i]
            for v in vals:
                match = oprtor(fmter(i), fmter(v))
                if match:
                    found_set.add(True)
                else:
                    found_set.add(False)
                if options.debug:
                    msg = '"{}" "{}" "{}" {}'
                    print_debug(msg, vals=(i, filter, v, match))

    return found_set


def match_by_keyword(targets, line, options):
    last = None
    last_found = None
    ln = split_line(line, options)
    found_set = set()
    cols = options.column
    if cols is None:
        cols = range(0, len(ln))
    for column in cols:
        try:
            t = ln[column].strip()
            if options.ignore_case:
                t = t.lower()
        except IndexError as e:
            raise e
        if t != last:
            last = t
            if options.substring_match is False:
                last_found = last in targets
            else:
                n_matches = 0
                for k in targets.keys():
                    if k in last:
                        n_matches += 1
                last_found = (n_matches == 1)
        found_set.add(last_found)

    return found_set


def match_by_range(targets, line, options):
    ln = split_line(line, options)
    if options.assume_chr is False:
        chrom = ln[options.chr_index]
    else:
        chrom = options.assume_chr
    pos = int(ln[options.pos_index])

    if chrom in targets:
        for r in targets[chrom]:
            if r[0] is None or r[1] is None:
                return set([True])
            if r[0] > pos:
                break
            elif r[1] >= pos:
                return set([True])
            else:
                continue

    return set([False])


def exit(*filehandles):
    for f in filehandles:
        if f is None:
            continue
        if f in [sys.stderr, sys.stdout, sys.stdin]:
            continue
        try:
            f.close()
        except:
            pass

    sys.exit(0)


def split_line(line, options):
    return line.strip('\n').split(options.sep)


def main():
    options = parse_options()
    infilename = options.infilename
    header = options.header
    outfilename = options.outfilename
    keep = options.keep
    remove = options.remove

    # make sure keep / remove are existing files
    for i in (keep, remove):
        if i is not False:
            if os.path.isfile(i) is False:
                msg = 'The file "{}" does not exist or is not readable.'
                print_error(msg, vals=[i])
                exit()

    # parse the column notation
    if options.column is not None:
        options.column = [
            int(i.strip()) - 1 for i in options.column.split(',')]

    # move the column indexes to 0-based indexing
    if options.pos_index is not False:
        options.pos_index -= 1
    if options.chr_index is not False:
        options.chr_index -= 1

    # set the delimiters
    sep = options.sep
    op_sep = sep
    if sep == 'tab':
        sep = '\t'
        op_sep = '\t'
    if sep == 'space':
        sep = ' '
        op_sep = ' '
    if sep == 'whitespace':
        sep = None
        op_sep = ' '
    options.sep = sep

    linecounter = 0
    n_removed = 0
    n_kept = 0

    input = None
    if infilename is False:
        input = sys.stdin
        infilename = 'STDIN'
    else:
        try:
            input = open(infilename, 'r')
        except IOError:
            print_error('File {} was not found.', vals=[infilename])
            sys.exit(0)

    output = None
    if outfilename is False:
        output = sys.stdout
    else:
        try:
            output = open(outfilename, 'w')
        except:
            print_error('File {} could not be opened for writing output.',
                        vals=[outfilename])
            exit(input)

    output_ex = None
    if options.outfilename_ex is not False:
        try:
            output_ex = open(options.outfilename_ex, 'w')
        except:
            print_error('File {} could not be opened for writing output.',
                        vals=[options.outfilename_ex])
            exit(input, output, output_ex)

    # handle the header
    header_line = None
    if header is True or options.by_col or options.filters is not False:
        linecounter += 1
        n_kept += 1
        header_line = input.readline()

    # if specifying --keep or --remove, read the corresponding files
    targets = None
    if options.filters is False:
        targets = get_targets(options)
        if targets is None:
            sys.exit(0)
    else:
        # make the filter dict using column names as keys
        options.filters = build_filters(options.filters)
        all_filters = []
        for i in options.filters:
            all_filters += options.filters[i].keys()

        # make sure that all specified column names are in the header
        filter_indexes = get_indexes(header_line, all_filters, options)
        for k in all_filters:
            if k not in filter_indexes:
                msg1 = 'The --filters key {} was not found on the header line.'.format(
                    k)
                msg2 = 'Maybe you forgot to specify the correct --sep?'
                print_error(msg1 + '\n' + msg2, vals=[k])
                exit(input, output, output_ex)

        # convert the keys from column names to column indexes
        filters = {}
        for f in iter(options.filters):
            filters[f] = {}
            for k, v in options.filters[f].items():
                i = filter_indexes[k]
                filters[f][i] = v
        options.filters = filters

    target_cols = []
    new_header_line = None
    if options.by_col:
        cols = split_line(header_line, options)
        for i in range(len(cols)):
            found = cols[i].strip() in targets
            if (found and keep is not False) or (not found and remove is not False):
                target_cols.append(i)
        new_header_line = op_sep.join([cols[i] for i in target_cols])

    do_keep = keep is not False or options.filters is not False
    do_remove = remove is not False and options.filters is False

    # choose the matching function
    if options.filters is not False:
        matching_fun = match_by_filters
    elif options.range:
        matching_fun = match_by_range
    else:
        matching_fun = match_by_keyword

    # write the header to the output first
    if options.by_col:
        output.write(new_header_line + '\n')
    elif options.header or options.filters is not False:
        output.write(header_line.rstrip('\n') + '\n')

    # then handle the rest of the input lines
    expected_col_n = None
    if header_line is not None:
        expected_col_n = len(split_line(header_line, options))
    for line in input:
        linecounter += 1
        if len(line.strip()) == 0:
            continue
        ln = split_line(line, options)
        if expected_col_n is None:
            expected_col_n = len(ln)
        else:
            if len(ln) != expected_col_n:
                msg = 'error: line {} had {} columns but the previous lines had {}.\n'
                msg = msg + 'This program only works if all of the lines in the input '
                msg = msg + 'have the same number of columns.\n'
                msg = msg + 'Maybe you are not using the correct --sep?'
                vals = (linecounter, len(ln), expected_col_n)
                print_error(msg, vals=vals)
                exit(input, output, output_ex)
        if options.by_col:
            n_kept += 1
            l = [ln[i] for i in target_cols]
            output.write(op_sep.join(l) + '\n')
            if options.outfilename_ex != False:
                l = [ln[i] for i in range(0, len(ln)) if i not in target_cols]
                output_ex.write(op_sep.join(l) + '\n')
        else:
            try:
                found_set = matching_fun(targets, line, options)
                found = False
                if True in found_set:
                    if options.match_all:
                        if False not in found_set:
                            found = True
                    else:
                        found = True

                if (found and do_keep) or (not found and do_remove):
                    output.write(line)
                    n_kept += 1
                else:
                    if options.outfilename_ex != False:
                        output_ex.write(line)
                    n_removed += 1

            except IndexError:
                msg = 'error: the file {} has only {} columns on line {},' \
                    ' which is less than the minimum amount of' \
                    ' columns implied by the --column value'
                vals = (infilename, len(ln), linecounter)
                print_error(msg + '\n' + line, vals=vals)
                exit(input, output, output_ex)

    # print final info
    if do_remove:
        action = 'removed'
        n = n_removed
    else:
        action = 'kept'
        n = n_kept
    msg = 'done, {} {} of the {} lines in {}'
    vals = (action, n, linecounter, infilename)
    sys.stderr.write(msg.format(*vals) + '\n')

    exit(input, output, output_ex)

if __name__ == '__main__':
    main()
