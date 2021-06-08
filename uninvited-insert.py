# encoding: ibm850 

import time
import sys
import collections

print 'Uninvited script inserter v0.9'
print '(C) 2016-2021 Erik Grahn J‰rlund'
print

rom_filename = "uninvited.nes"

a = raw_input("Insert which chunk [0-2]? ")

if a == "0":
	chunk_no = 0
elif a == "1":
	chunk_no = 1
elif a == "2":
	chunk_no = 2
else:
	print "Invalid chunk number, aborting."
	exit(1)
	
a = raw_input("Read frequency table from ROM or analyze chunk and write a new one [R, W]? ")

if a[0] == "r" or a[0] == "R":
	rom = open(rom_filename, 'r+b')

	frequency_table = []

	hdr = 0x10

	sys.stdout.write("Reading frequency table...")
	
	rom.seek(0x1E42F + hdr)
	
	for i in range(64):
		frequency_table.append(ord(rom.read(1)))
	
	rom.close()
	
	print "Done."
	
	write_table = False
elif a[0] == "w" or a[0] == "W":
	write_table = True	
else:
	print "Invalid choice, aborting."
	exit(1)

lasttag = "end"

def parse_tag(tag):
	global infile, lasttag
	
	tags = {'cls':0x1C, 'br':0x1D, 'end': 0x1F, 'insert': 0xFE}
	
	rest = infile.read(len(tag))

	if rest == tag[1:] + '>':
		lasttag = tag
		return chr(tags[tag])
	else:
		die("Expected <"+tag+">, found unknown or malformed tag. Aborting.", infile.tell())

	return out_char

def die(msg, pos):
	print "\n" + msg
	print "Parsing failed at position", pos
	exit(1)

def word2bytes(w):
	return divmod(w, 0x100)

chunk_sizes = {0: 13056, 1: 11776, 2: 7680} # space available in the three script data chunks
chunk_ptr_base = {0: 0x8200, 1: 0x8200, 2: 0xA200} # why are the pointers offset by 0x2000 bytes for chunk 2? no idea.
ptr_table_addresses = {0: 0x8000, 1: 0xC000, 2: 0x16000}

print 'Parsing input files...'

charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ " + chr(0xFF) + chr(0x1C) + chr(0x1D) + chr(0x1E) + chr(0x1F) + ".-*=:,\"!?;'$()+" + chr(0xFF) + "0123456789èéôê" + chr(0xFF) + chr(0xFE)
# 0xFE is actually control code 0x3F but changed here since it otherwise conflicts with the question mark (which is ascii 0x3F)

# tiles in the same order as the charset
tiles = [0xb1, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0xba, 0xbb, 0xbc, 0xbd, 0xbe, 0xbf, 0xc0, 0xc1, 0xc2, 0xc3, 0xc4, 0xc5, 0xc6, 0xc7, 0xc8, 0xc9, 0xca, 0xb0, 0x0b, 0x0c, 0x0d, 0x7e, 0x0f, 0xa1, 0xa4, 0xa3, 0xcb, 0xd6, 0xd8, 0xd0, 0x8a, 0x8b, 0xd7, 0xcd, 0xcc, 0xd9, 0xda, 0xa5, 0x7e, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8c, 0x8d, 0x8e, 0x8f, 0x04, 0x12, 0x20]

rawscript = ''	# the raw script in one huge string
encscript = ''	# the encoded script as a really huge string of ones and zeros.

curstring_read = 0	# the current string index, as read from the file
curstring_calc = -1 # the current string index, as counted by the loop

#with open('uninvited-dump'+str(chunk_no)+'.txt', 'rb') as infile:

with open('uninvited-dump'+str(chunk_no)+'-translated.txt', 'rb') as infile:
	sys.stdout.write('Parsing strings in chunk ' + str(chunk_no) + '...')

	c = infile.read(1)

	while c != '':
		if c == '[':
			if not lasttag == "end":
				print "WARNING: unterminated string", curstring_calc
			
			lasttag = ""
			
			rest = infile.read(2)

			if rest[0].isdigit() and rest[1] == ']': 
				curstring_read = int(rest[0])
				curstring_calc += 1
				
				if curstring_read == curstring_calc:
					sys.stdout.write("\b\b\b." + str(curstring_read).zfill(3))
				else:
					die("String index mismatch, string skipped? Expected " + str(curstring_calc) + ", got " + str(curstring_read), infile.tell())
					
			elif rest.isdigit():
				rest_of_rest = infile.read(1)
				if rest_of_rest == ']':
					curstring_read = int(rest)
					curstring_calc += 1
					
					if curstring_read == curstring_calc:
						sys.stdout.write("\b\b\b." + str(curstring_read).zfill(3))
					else:
						die("String index mismatch, string skipped? Expected " + str(curstring_calc) + ", got " + str(curstring_read), infile.tell())
				else:
					rest_of_rest_of_rest = infile.read(1) # lol
					
					if rest_of_rest_of_rest == ']':
						curstring_read = int(rest + rest_of_rest)
						curstring_calc += 1
						
						if curstring_read == curstring_calc:
							sys.stdout.write("\b\b\b." + str(curstring_read).zfill(3))
						else:
							die("String index mismatch, string skipped? Expected " + str(curstring_calc) + ", got " + str(curstring_read), infile.tell())								
					else:
						die("Parse error: expected ']'", infile.tell())

		elif c == '<':
			c = infile.read(1)
			
			if c == 'c': rawscript += parse_tag('cls')				
			elif c == 'b': rawscript += parse_tag('br')
			elif c == 'e': rawscript += parse_tag('end')
			elif c == 'i': rawscript += parse_tag('insert')
					
			elif c.isdigit():
				# insert a literal byte
				rest = infile.read(1)

				if rest == '>': 
					# one digit byte literal
					rawscript += chr(int(c))
				elif rest.isdigit():
					# two digit byte literal
					rawscript = rawscript + chr(int(c + rest))
				else:
					die("Expected byte literal, found unknown tag. Aborting.", infile.tell())
				
		elif c == '\n' or c == '\r':
			pass # ignore cr and lf
			
		elif c in charset:
			rawscript += c
			
		else:
			"Illegal character at position", infile.tell(), "aborting."
					
		c = infile.read(1)

print 
print "Parsed", len(rawscript), "characters in", curstring_read, "strings."


if write_table:
	print
	print 'Generating frequency tables...'
	frequencies = collections.Counter(rawscript)

	frequency_table = []

	# the frequency table from the original ROM. used for debugging
	frequency_table_stock = [0x1a, 0x04, 0x13, 0x0e, 0x12, 0x00, 0x08, 0x0d, 0x11, 0x07, 0x0b, 0x14, 0x03, 0x1d, 0x18, 0x20, 0x02, 0x0c, 0x06, 0x1f, 0x05, 0x0f, 0x16, 0x01, 0x0a, 0x2a, 0x15, 0x25, 0x1c, 0x26, 0x27, 0x21, 0x17, 0x19, 0x10, 0x09, 0x28, 0x3f, 0x24, 0x2c, 0x2d, 0x32, 0x39, 0x29, 0x30, 0x37, 0x38, 0x34]

	for item in frequencies.most_common():
		c = item[0]
		
		if(charset.find(c) == -1):
			if ord(c) == 0x05 or ord(c) == 0x14 or ord(c) == 0x15:
				print "Notice: not adding item control character", hex(ord(c)), "to frequency table"
			else:
				print "Warning: unrecognized character", hex(ord(c)), "does not appear in character set."
				print "This might be bad news."
		else:
			frequency_table.append(charset.find(c))

	print "Frequency table generated."	
	print "Total length of character set:", len(charset)
	print "Number of characters in table:", len(frequency_table)
else:
	print "Skipping frequency table generation."

print 'Generating character encodings...'

binary_enc = []

for i in xrange(256):
	binary_enc.append("")
	
	z = i >> 3
	lo = i - (8 * z)

	for j in range(z):
		binary_enc[i] += '0'
		
	binary_enc[i] += '1'
		
	binary_enc[i] += "{0:03b}".format(lo)
print "Done generating."
print

print 'Compressing script...'

string_addresses = []
string_addresses.append(chunk_ptr_base[chunk_no])

size = 0
strings = 0

for c in rawscript:
	if ord(c) == 0x05 or ord(c) == 0x14 or ord(c) == 0x15: # control byte found
		encscript += "{0:08b}".format(ord(c)) # append this byte to the script
		size += 8
		continue

	size += len(binary_enc[frequency_table.index(charset.find(c))])
	encscript += binary_enc[frequency_table.index(charset.find(c))]

	if ord(c) == 0xFE and strings > 127 and chunk_no == 2: # special strings only, ugly hack
		while not (size % 8) == 0: # skip to next byte offset, padding with zeroes as we go
			encscript += '0'
			size += 1

	if ord(c) == 0x1F:
		while not (size % 8) == 0: # skip to next byte offset, padding with zeroes as we go
			encscript += '0'
			size += 1
		# SUPER HACK: never insert a full byte of zeroes because reasons
		#             unless the previous byte was 0x20 because other reasons
		#if encscript[-8:] == "00000000" and ord(prevc) != 0x20:
			#print "!!! its here !!!",
			#encscript = encscript[:-8]
			#size -= 8
			
		if ord(c) == 0x1F:
			# end of string marker; the current address will be the start of the next string
			string_addresses.append(chunk_ptr_base[chunk_no] + size/8)
			strings += 1
	
	prevc = c
	
while not (size % 8) == 0:  # make sure to end on an even byte!
	encscript += '0'
	size += 1
			
size_bytes = size/8
	
print "   Raw script size:", len(rawscript), "bytes"
print "   Compressed size:", size_bytes, "bytes =", "{0:.1f}%".format(size_bytes/float(len(rawscript)) * 100), "of original size"
print
print "Available in chunk:", chunk_sizes[chunk_no], "bytes"
if size_bytes > chunk_sizes[chunk_no]:
	print "Not enough space in script chunk",chunk_no,"- your script is too large!"
	exit(1)
print " Free after insert:", chunk_sizes[chunk_no] - size_bytes, "bytes"
print

print 'Generating pointers...'

pointer_table = ""

count = 0

for address in string_addresses[:-1]: # skip the last address, it will point beyond the last string
	hi, lo = word2bytes(address)
	
	if count/2 == 114 and chunk_no == 1:
		# address the fact that there are thirteen ERROR entries in the middle of chunk 1 that all point to the same string
		# so there are actually only 242 unique strings in chunk 1 but 256 entries in the pointer table
		print "Special case: repeating ERROR string pointer 13 extra times. Don't worry about it."

		for nothing in range(13):
			pointer_table += chr(lo)
			pointer_table += chr(hi)
			count += 2
			
	pointer_table += chr(lo)
	pointer_table += chr(hi)
	
	count += 2
	
while count < 512:
	pointer_table += chr(lo) # pad it.
	pointer_table += chr(hi) # just pad it.
	count += 2

print len(pointer_table), "byte pointer table generated."
print 

print
print 'Inserting script...'
print

rom = open(rom_filename, 'r+b')

hdr = 0x10

sys.stdout.write("Inserting frequency table...")
rom.seek(0x1E42F + hdr)

for byte in frequency_table:
	rom.write(chr(byte))

print "done. Wrote", rom.tell() - (0x1E42F + hdr), "bytes."

sys.stdout.write("Inserting tile translation table...")
rom.seek(0x1DC37 + hdr)

for byte in tiles:
	rom.write(chr(byte))

print "done. Wrote", rom.tell() - (0x1DC37 + hdr), "bytes."


sys.stdout.write("Inserting pointer table for chunk " + str(chunk_no) + " at " + str(hex(ptr_table_addresses[chunk_no])) + "...")
rom.seek(ptr_table_addresses[chunk_no] + hdr)
oldpos = rom.tell()
rom.write(pointer_table)
print "done. Wrote", rom.tell() - oldpos, "bytes."

sys.stdout.write("Inserting actual script...")

count = 0

for char in encscript:
	if len(encscript) == 0: break
	
	rom.write(chr(int(encscript[:8], 2)))
	encscript = encscript[8:]
	count += 1

print "done. Wrote", count, "bytes."

print
print "Insertion complete!"
print
