# %%

import csv
import pandas as pd

input_filename = '/Users/michaelweinold/Downloads/IOT_2014_pxp/A.txt'  # Changed extension for clarity, can be .txt
output_filename = 'out.txt'
rows_to_keep = 13
cols_to_keep = 12

with open(input_filename, 'r', newline='') as infile, \
     open(output_filename, 'w', newline='') as outfile:

    reader = csv.reader(infile, delimiter='\t') # Specify tab delimiter
    writer = csv.writer(outfile, delimiter='\t') # Specify tab delimiter

    for i, row in enumerate(reader):
        if i < rows_to_keep:
            writer.writerow(row[:cols_to_keep])
        else:
            # Stop reading once we have processed the desired number of rows
            break


df = pd.read_csv(output_filename, sep='\t', header=None)

# %%

input_filename = '/Users/michaelweinold/Downloads/IOT_2014_pxp/satellite/S.txt'  # Changed extension for clarity, can be .txt
output_filename = 'out.txt'
rows_to_keep = 13
cols_to_keep = 11

with open(input_filename, 'r', newline='') as infile, \
     open(output_filename, 'w', newline='') as outfile:

    reader = csv.reader(infile, delimiter='\t') # Specify tab delimiter
    writer = csv.writer(outfile, delimiter='\t') # Specify tab delimiter

    for i, row in enumerate(reader):
        if i < rows_to_keep:
            writer.writerow(row[:cols_to_keep])
        else:
            # Stop reading once we have processed the desired number of rows
            break


df = pd.read_csv(output_filename, sep='\t', header=None)

# %%

input_filename = '/Users/michaelweinold/Downloads/IOT_2014_pxp/impacts/S.txt'  # Changed extension for clarity, can be .txt
output_filename = 'out.txt'
rows_to_keep = 13
cols_to_keep = 11

with open(input_filename, 'r', newline='') as infile, \
     open(output_filename, 'w', newline='') as outfile:

    reader = csv.reader(infile, delimiter='\t') # Specify tab delimiter
    writer = csv.writer(outfile, delimiter='\t') # Specify tab delimiter

    for i, row in enumerate(reader):
        if i < rows_to_keep:
            writer.writerow(row[:cols_to_keep])
        else:
            # Stop reading once we have processed the desired number of rows
            break


df = pd.read_csv(output_filename, sep='\t', header=None)