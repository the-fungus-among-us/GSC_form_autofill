#!/usr/bin/env/python3

## LOAD DEPENDENCIES
import csv
import os

## GET USER DATA
path = input("Provide a filepath for the data you wish to process:")
reference = input("Provide a filepath for your index sequence database:")
filename = input("Provide a filepath to store output:")

## MAKE A DICTIONARY OF SAMPLES IDS AND THEIR ASSOCIATED INDEX IDS
def create_sample_index(path):

	## initialize variables/lists/dictionaries
	sample_dict={}
	line_num = 0
	empty_cells = 0
	empty_cell_list = []

	## read provided data to be processed
	with open(path) as data:
		lines = data.readlines()

	while line_num < len(lines):
		line = lines[line_num].strip()

		## for every header line, extract the plate name, project name, and amplicon type
		if ":" in line:
			plate = line.split(':')[0]
			project = line.split(' ')[1]
			header=line.split(':')[1]
			amplicon = header.split(' ')[-1]

			## for every non-header line, extract sample IDs and their associated index IDs
			for row in lines[line_num+2:line_num+10]:
				cells = row.strip().split(',')
				column_num = 0

				## for each sample, create a dictionary entry with its name (format: project name_amplicon type_sample ID)
				## and index IDs (format: plate name_row name_column name)
				for cell in cells[1:12]:
					column_num+=1
					index_letter = cells[0]
					header_row = lines[line_num+1]
					index_number = header_row.split(',')[column_num]
					index_num = "".join(["0",index_number.strip()])
					indices = "_".join([plate,index_letter,index_num[-2:]])

					if cell.strip():
						sample_name = "_".join([project,amplicon,cell])
						sample_dict[sample_name] = indices
					else:
						empty_cells = empty_cells + 1
						empty_cell_list.append(indices)
		line_num+=1

	return sample_dict, empty_cells, empty_cell_list

sample_dict, empty_cells, empty_cells_list = create_sample_index(path)

## MAKE A DICTIONARY OF INDEX IDS AND THEIR ASSOCIATED SEQUENCES
def make_index_dictionary(reference):

	## initialize dictionary
	index_dict={}

	## for every pair of indices in the sequence database, create a dictionary entry with its index IDs and sequences
	with open(reference) as database:
		for line in database:
			indices=line.split(',')[0]
			fields = line.split(',')
			sequences = (fields[2].strip(), fields[1].strip())
			index_dict[indices]=sequences
	return index_dict

## MATCH SAMPLES TO THEIR INDEX SEQUENCES
def match_and_group(path, reference):

	## initialize variables/lists/dictionaries
	index_dict = make_index_dictionary(reference)
	unique_dict = {}
	output = []

	## for each sample, create a dictionary entry with its name and index sequences
	## combine sample names as necessary to ensure only one dictionary entry exists for each unique pair of indices
	for sample_id, index_id in sample_dict.items():
		if index_id in index_dict:
			if index_id in unique_dict:
				unique_dict[index_id] += "-" + sample_id
			else:
				unique_dict[index_id] = sample_id

		## report index ids that are present in the data but absent in the sequence database
		else:
			print(f"Error: {index_id} not recognized")

	## convert the dictionary to a list for downstream applications
	for index_id, sample_ids in unique_dict.items():
		i7, i5 = index_dict[index_id]
		output.append(f"{sample_ids},{i7},{i5}")
	return output

## WRITE SORTED DATA TO A CSV
def write_output(filename, path, reference):

    ## initialize variables
    rows = match_and_group(path, reference)
    fields = [row.strip().split(',') for row in rows]
    column_titles = ["Sample Name", "i7 Sequence", "i5 Sequence-FWD"]

    ## write csv file
    with open(filename, "w", newline="", encoding="utf-8") as source:
        writer = csv.writer(source, delimiter=",")
        writer.writerow(column_titles)
        writer.writerows(fields)

write_output(filename, path, reference)

## CREATE A TEXT DOCUMENT LISTING THE LOCATIONS OF EMPTY CELLS
empty_cell_dir = os.path.dirname(path)
empty_cell_file = os.path.join(empty_cell_dir, "emptycells.txt")
with open(empty_cell_file,"w") as destination:
	for item in empty_cells_list:
		destination.write(f"{item}\n")

## PRINT DIAGNOSTICS
print(f"{empty_cells} empty cells skipped (see emptycells.txt for locations)")
print(f"{len(make_index_dictionary(reference))-1} unique index pairs detected in {reference.split('/')[-1]}")
print(f"{len(sample_dict)} samples and {len(match_and_group(path,reference))} unique index pairs detected in {path.split('/')[-1]}")
print(f"File saved as {filename}")
