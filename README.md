# filter_lines

DESCRIPTION

Use filter_lines.py to extract lines from input based on keywords or values
in named columns. Functions as a general utility. Has a shortcut for
geneticists to filter by genomic ranges.

Examples:

A. Filter the file "big_file.txt" by keeping all lines which contain any of the words 
listed in the file "words.txt". Assume the file to be filtered contains data in columns 
separated by spaces. Only use the values in the first column of "big_file.txt" to 
look for matches. 

> filter_lines.py --in big_file.txt --keep words.txt --sep space --column 1 --out filtered_file.txt

B. Filter a file by values in colums. Assume the columns are named on the first (header)
line of the input file. Output the header line and lines where either the "weight" column has a value
greater than 13, or the value of the "taste" column is "good", or both.

> filter_lines.py --in big_file.txt --filters "weight>13,taste=good" --sep space --column 1 --out filtered_file.txt

C. As above but now keep only lines where the "weight" column has a value greater than 13 and 
the value of the "taste" column is "good".

> filter_lines.py  --match-all --in big_file.txt --filters "weight>13,taste=good" --sep space --column 1 --out filtered_file.txt


REQUIREMENTS

Python 2.7 or newer.


INSTALLATION

Copy the file filter_lines.py to a folder. To execute, type:
python path/to/filter_lines.py --help

