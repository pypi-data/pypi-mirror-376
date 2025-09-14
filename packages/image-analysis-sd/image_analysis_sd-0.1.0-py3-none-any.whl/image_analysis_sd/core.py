import subprocess
import sys
import os
import datetime
import pathlib
WORDCOUNT=1000
IMG_TYPES=['.jpg','.png']
TXT_TYPES=['.md']
VALID_TYPES=[g for f in [IMG_TYPES,TXT_TYPES] for g in f]
EXIT_CODE=0
def safefilepath(path:str):
	(parent_path,name) = os.path.split(path)
	safename=''.join((f if (f.isalnum()) else '_') for f in name)
	return f"{parent_path}/{safename}"
def is_valid_type(file_path:str):
	(_,ext) = os.path.splitext(file_path)
	return ext.lower() in VALID_TYPES
def is_valid_image_type(file_path:str):
	(_,ext) = os.path.splitext(file_path)
	return ext.lower() in IMG_TYPES
def is_valid_text_type(file_path:str):
	(_,ext) = os.path.splitext(file_path)
	return ext.lower() in TXT_TYPES
def filter_text_files(file_paths:list[str]):
	return [g for f in file_paths for g in ([f] if is_valid_text_type(f) else [])]
def filter_image_files(file_paths:list[str]):
	return [g for f in file_paths for g in ([f] if is_valid_image_type(f) else [])]
def filter_image_text_files(file_paths:list[str]):
	return (filter_image_files(file_paths=file_paths),filter_text_files(file_paths=file_paths))
PROMPT="""
Based on the following description provide information suitable for recreating it in InvokeAI.  Include the following: Positive Prompt, Negative Prompt (Be as detailed here as you need to be for good fidelity), Step Count, CFG Scale, Suggested Image Dimensions, and an idea on the best stable diffusion model to use and the best scheduler.:

Here is the Description: 
XDESCRIPTIONX
"""
PROMPT2="""
Provide an incredibly detailed and nuanced description of the image (XFILEX).  Focus on the following:

*   **Overall Composition:** Describe the arrangement of elements, the use of space, and the overall balance of the image.
*   **Objects & Figures:** For each significant object or figure:
    *   Describe its physical characteristics (size, shape, color, texture, material).
    *   Describe its position and orientation in relation to other objects.
    *   Describe the lighting and shadows affecting it.
    *   Infer possible textures and materials based on visual cues (e.g., 'the fabric appears to be silk,' 'the surface looks rough and weathered').
*   **Implied Sensory Details:**  Based on the visual information, what textures might you feel if you could touch the objects? What sounds might be associated with the scene? (Be speculative, but grounded in the image.)
*   **Relationships & Interactions:** Describe how the objects and figures interact with each other.  What is the implied narrative or story suggested by the composition?

Present your response in well-structured paragraphs. Prioritize accurate visual description over imaginative interpretation.  Avoid making assumptions about the context unless directly supported by visual evidence.  Focus on objectivity. Aim for a description that is at least""" + f'{WORDCOUNT}' +  """words long.
"""
PROMPT3="""
Provide an incredibly detailed and nuanced description of a new, composite image created by seamlessly blending the elements of the provided images (XFILESX) together.  Focus on the following:

*   **Overall Composition:** Describe the arrangement of elements, the use of space, and the overall balance of the image.
*   **Objects & Figures:** For each significant object or figure:
    *   Describe its physical characteristics (size, shape, color, texture, material).
    *   Describe its position and orientation in relation to other objects.
    *   Describe the lighting and shadows affecting it.
    *   Infer possible textures and materials based on visual cues (e.g., 'the fabric appears to be silk,' 'the surface looks rough and weathered').
*   **Implied Sensory Details:**  Based on the visual information, what textures might you feel if you could touch the objects? What sounds might be associated with the scene? (Be speculative, but grounded in the image.)
*   **Relationships & Interactions:** Describe how the objects and figures interact with each other.  What is the implied narrative or story suggested by the composition?

Present your response in well-structured paragraphs. Prioritize accurate visual description over imaginative interpretation.  Avoid making assumptions about the context unless directly supported by visual evidence.  Focus on objectivity. Aim for a description that is at least""" + f'{WORDCOUNT}' +  """words long.
"""
PROMPT4="""
Provide an incredibly detailed and nuanced description of described situation.  Focus on the following:

*   **Overall Composition:** Describe the arrangement of elements, the use of space, and the overall balance of the image.
*   **Objects & Figures:** For each significant object or figure:
    *   Describe its physical characteristics (size, shape, color, texture, material).
    *   Describe its position and orientation in relation to other objects.
    *   Describe the lighting and shadows affecting it.
    *   Infer possible textures and materials based on visual cues (e.g., 'the fabric appears to be silk,' 'the surface looks rough and weathered').
*   **Implied Sensory Details:**  Based on the visual information, what textures might you feel if you could touch the objects? What sounds might be associated with the scene? (Be speculative, but grounded in the image.)
*   **Relationships & Interactions:** Describe how the objects and figures interact with each other.  What is the implied narrative or story suggested by the composition?

Present your response in well-structured paragraphs. Prioritize accurate visual description over imaginative interpretation.  Avoid making assumptions about the context unless directly supported by visual evidence.  Focus on objectivity. Aim for a description that is at least""" + f'{WORDCOUNT}' +  """words long.

Now, here is the situation:

XSITUATIONX
"""
PROMPT5=f"Provide an incredibly detailed new, narrative based on the following, while aiming for a length of {WORDCOUNT} words:\n\nXSITUATIONSX"

PROMPT6=f"Provide an incredibly detailed new, narrative based on the following, while aiming for a length of {WORDCOUNT*2} words:\n\nXSITUATIONSX"
MODEL='biggemma3:latest'
MODEL2='biggemma3:latest'
def reverse_sd(file:str,description:str):
	rprompt = PROMPT.replace('XDESCRIPTIONX',description)
	outfile=f"{safefilepath(f"{file}.simple_reverse_diffusion_{MODEL}")}.md"
	command = [
            "ollama",
            "run",
            MODEL,			
            "--",			
            rprompt            
        ]
	result = subprocess.run(command, capture_output=True, text=True, check=True)
	info = result.stdout
	print(f'Writing to sd info to `{outfile}`:\n{info}')
	with open(outfile,'w') as f:
		f.write(info)
def describe(file:str):
	rprompt = PROMPT2.replace('XFILEX',os.path.abspath(file))
	outfile=f"{safefilepath(f"{file}.description_{MODEL}")}.md"
	command = [
            "ollama",
            "run",
            MODEL2,
            "--",
            rprompt            
        ]
	result = subprocess.run(command, capture_output=True, text=True, check=True)
	info = result.stdout
	print(f'Writing description to `{outfile}`:\n{info}')
	with open(outfile,'w') as f:
		f.write(info)
	return info
def describe_situation(situation_file:str,write_file:bool=True):
	with open(situation_file) as situation_file_io:
		situation_text = situation_file_io.read()
	rprompt = PROMPT4.replace('XSITUATIONX',situation_text)
	outfile = f"{safefilepath(f"{situation_file}.description_{MODEL2}")}.md"
	command = [
            "ollama",
            "run",
            MODEL2,
            "--",
            rprompt            
        ]
	result = subprocess.run(command, capture_output=True, text=True, check=True)
	info = result.stdout
	if (write_file):
		print(f'Writing description to `{outfile}`:\n{info}')
		with open(outfile,'w') as f:
			f.write(info)
	else:
		print(f'Considering description:\n{info}')
	return info
def describe_situations(situation_files:list[str],outfile:str=None):
	if len(situation_files) < 2:
		return describe_situation(situation_files[0],outfile)
	def load_sitation(file:str):
		with open(file) as fio:
			return fio.read()
	situations_texts = [load_sitation(f) for f in situation_files]
	compendum_of_sitatutions = ""
	situation_index = 1
	for f in situations_texts:
		compendum_of_sitatutions += f"{f}\n\n"
		situation_index += 1
	rprompt = PROMPT5.replace('XSITUATIONSX',compendum_of_sitatutions)
	if outfile is not None:
		outfile = f"{safefilepath(f"{outfile}.description_{MODEL2}")}.md"
	command = [
            "ollama",
            "run",
            MODEL2,                        
        ]
	
	result = subprocess.Popen(command, stdout=subprocess.PIPE,stdin=subprocess.PIPE, text=True)	
	info,_ = result.communicate(rprompt)
	
	if outfile is not None:
		print(f'Writing description to `{outfile}`:\n{info}')
		with open(outfile,'w') as f:
			f.write(info)
	else:
		print(f'Considering description:\n{info}')
	return info
def describe_situations_raw(situations:list[str],double_detailed:bool=False):
	if len(situations) < 2:
		return situations[0]
	situations_texts = situations
	compendum_of_sitatutions = ""
	situation_index = 1
	for f in situations_texts:
		compendum_of_sitatutions += f"${f}\n"
		situation_index += 1
	rprompt = PROMPT5.replace('XSITUATIONSX',compendum_of_sitatutions)	if not double_detailed else PROMPT6.replace('XSITUATIONSX',compendum_of_sitatutions)
	command = [
            "ollama",
            "run",
            MODEL2,
            "--",
            rprompt            
        ]
	result = subprocess.run(command, capture_output=True, text=True, check=True)
	info = result.stdout
	print(f'Considering Situation:\n{info}')
	
	return info

def describe_mixed_situtations(mixed_situation_files: list[str],outfilex:str):
	outfile=f"{safefilepath(f'{outfilex}.description_{MODEL}')}.md"
	
	(img_files,txt_files) = filter_image_text_files(mixed_situation_files)	
	has_imgs = len(img_files) > 0
	has_txt = len(txt_files) > 0
	if (has_imgs and has_txt):
		img_combo = describe_smash(img_files)
		txt_combo = describe_situations(txt_files)
		master_description=describe_situations_raw([img_combo,txt_combo],double_detailed=True)
	elif (has_imgs):
		master_description= describe_smash(img_files)
	elif (has_txt):
		master_description=describe_situations(txt_files) 
	else:
		return None
	if (outfilex) is not None:
		print(f'Writing description to `{outfile}`:\n{master_description}')
		with open(outfile,'w') as f:
			f.write(master_description)
	else:
		print(f'Considering description:\n{master_description}')
	return master_description


def describe_smash(files:list[str],outfilex:str=None):
	rprompt = PROMPT3.replace('XFILESX',",".join((os.path.abspath(file) for file in files)))
	if outfilex is not None:
		outfile=f"{safefilepath(f'{outfilex}.description_{MODEL}')}.md"
	command = [
            "ollama",
            "run",
            MODEL2,
            "--",
            rprompt            
        ]
	result = subprocess.run(command, capture_output=True, text=True, check=True)
	info = result.stdout
	if (outfilex) is not None:
		print(f'Writing description to `{outfile}`:\n{info}')
		with open(outfile,'w') as f:
			f.write(info)
	else:
		print(f'Considering description:\n{info}')
	return info

def helpme():
	help_text="""
shard-sd (-h) -o OUTPUT_FILE INPUT_FILE.md INPUT_FILE_2.jpg INPUT_FILE_3.png ...
	-h Brings up this help
	-o Specifies the output file basepath/basename (Do not add a file extension, program will do that for you.)
	OUTPUT_FILE The output file of your choosing
	INPUT_FILE.md INPUT_FILE_2.jpg INPUT_FILE.png The input files of your choosing.
"""
	sys.stderr.write(help_text)
def main():
	if 'RSD_MODEL' in os.environ.keys():
		global MODEL
		MODEL = os.environ['RSD_MODEL']

	if len(sys.argv) > 1:
		pargz=sys.argv[1:]
		outfile=None
		needhelp=False
		if '-o' in pargz:
			idxO = pargz.index('-o')
			if idxO < len(pargz)-1:
				outfile = pargz[idxO+1]
				outfile = os.path.abspath(outfile)
				pargz = pargz[:idxO] + pargz[idxO+2:]
		if '-h' in pargz:
			needhelp=True
		if outfile is None:
			sys.stderr.write("Error No output file specified. (Specify it by using the -o flag)\n")
			needhelp=True
			EXIT_CODE=1
		if len(pargz) == 0:
			sys.stderr.write("Error No input files specified.\n")
			EXIT_CODE=2
		if needhelp:
			helpme()
			return
		

		dt=datetime.datetime.now()
		(year,month,day,hours,minutes,seconds,milliseconds) = (dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second,dt.microsecond//1000)
		(year_precision,month_precision,day_precision,hour_precision,minute_precision,second_precision,millisecond_precision) = (4,2,2,2,2,2,3)
		def stringize_date_component(date_component,length):
			o = f"{date_component}"
			while len(o) < length:
				o = f"0{o}"
			return o
		
		(year_str,month_str,day_str,hour_str,minute_str,seconds_str,millisecond_str) = map(stringize_date_component,(year,month,day,hours,minutes,seconds,milliseconds),
																					 (year_precision,month_precision,day_precision,hour_precision,minute_precision,second_precision,millisecond_precision)
																					 )
		
		outfile=f"{outfile}_{year_str}{month_str}{day_str}_{hour_str}{minute_str}{seconds_str}_{millisecond_str}.txt"
		descr = describe_mixed_situtations(sys.argv[1:],outfilex=outfile)
		if descr is not None:
			reverse_sd(outfile,descr)
		else:
			sys.stderr.write("No Description Returned: I cannot can't reverse stable diffusion nothing.\n")
			sys.stderr.write("Filenames supplied:\n")
			for f in sys.argv[1:]:
				sys.stderr.write(f'\t{f}')
				if is_valid_type(f):
					print(' ✅\n')
				else:
					print(' ❌\n')
			sys.stderr.write('Sorry! Exiting With Error Status...')
			exit(1)
	# elif len(sys.argv) > 2:
	# 	dt=datetime.datetime.now()
	# 	(year,month,day,hours,minutes,seconds,milliseconds) = (dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second,dt.microsecond//1000)
	# 	(year_precision,month_precision,day_precision,hour_precision,minute_precision,second_precision,millisecond_precision) = (4,2,2,2,2,2,3)
	# 	def stringize_date_component(date_component,length):
	# 		o = f"{date_component}"
	# 		while len(o) < length:
	# 			o = f"0{o}"
	# 		return o
		
	# 	(year_str,month_str,day_str,hour_str,minute_str,seconds_str,millisecond_str) = map(stringize_date_component,(year,month,day,hours,minutes,seconds,milliseconds),
	# 																				 (year_precision,month_precision,day_precision,hour_precision,minute_precision,second_precision,millisecond_precision)
	# 																				 )
		
	# 	outfile=f"sd_smash_{year_str}{month_str}{day_str}_{hour_str}{minute_str}{seconds_str}_{millisecond_str}.txt"
	# 	descr = describe_smash(sys.argv[1:],outfile)
	# 	reverse_sd(outfile,descr)
	

if __name__ == '__main__':
	main()
	if EXIT_CODE != 0:
		exit(EXIT_CODE)
