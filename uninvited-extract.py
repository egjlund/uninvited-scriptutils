# encoding: ibm850

import bitio

rom_filename = "uninvited.nes"

#
# NOTE: as of now, this can ONLY be relied on to dump the stock script --
# or, rather: only scripts using the default frequency table. this means
# you can not insert a custom script and then dump it back out if you have
# modified the frequency table.
#

print "Uninvited script dumper v0.9"
print "(C) 2016-2021 by Erik Grahn Järlund"
print

a = raw_input("Include debug info in script (Y/N)? ")

if a[0] == "y" or a[0] == "Y":
	debug = True
else:
	debug = False


# offsets where the text chunks start, relative to 0x8000 (the very start of text data)
base_addresses = [0x0000, 0x4000, 0xE000]
num_strings = [256, 243, 148]

# this is the stock translation table with letters sorted by usage frequency (huffman encoding)
table = [0x1A, 0x04, 0x13, 0x0E, 0x12, 0x00, 0x08, 0x0D, 0x11, 0x07, 0x0B, 0x14, 0x03, 0x1D, 0x18, 0x20, 0x02, 0x0C, 0x06, 0x1F, 0x05, 0x0F, 0x16, 0x01, 0x0A, 0x2A, 0x15, 0x25, 0x1C, 0x26, 0x27, 0x21, 0x17, 0x19, 0x10, 0x09, 0x28, 0x3F, 0x24, 0x2C, 0x2D, 0x32, 0x39, 0x29, 0x30, 0x37, 0x38, 0x34]


#
# this is the character set. it is 64 characters, some of which are unused or control characters
# 
# 0x1C is clear screen		its place is marked by ^ in the character set 	it is output to the dump as '<cls>'
# 0x1D is line break		its place is marked by # in the character set 	it is output to the dump as '<br>'
# 0x1F is end of string		its place is marked by @ in the character set 	it is output to the dump as '<end>'
# 0x3F is insert item name	its place is marked by % in the character set	it is output to the dump as '<insert>'
#
#    _ are all unused (?)
#    + is actually a mid-dot in CHR ROM, unused as far as I know
#

charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ _^#_@.-*=:,\"!?;'$()+_0123456789_____%"
		  #0123456789ABCDEF0123456789ABCDEF012345 6789ABCDEF0123456789ABCDEF
          #01234567890123456789012345678901234567 89012345678901234567890123
          
# these are the addresses in memory where the strings are found, read from a table in ROM 
offsets = []



f = open(rom_filename, 'rb')


base_offset = 0x8010

for chunk_no in range(3):
	offsets = []
	
	print "Processing text chunk", chunk_no
	outfile = open('uninvited-dump' + str(chunk_no) + '.txt', 'wb')

	chunk_offset = base_addresses[chunk_no]

	r = BitReader(f)

	f.seek(base_offset + chunk_offset) # start of text chunk

	if debug: outfile.write("<pointers>\n")
	
	for i in xrange(0x100):
		# read 512 bytes of string pointers
		byte1 = r.readbits(8)
		byte2 = r.readbits(8)
		
		# to create our 16-bit offset, we need to swap the byte order of the bytes we just read
		o = (byte2 << 8) + byte1
		
		offsets.append(o)
		if debug: outfile.write(str(hex(o)) + " ")

	if debug: outfile.write("\n</pointers>\n\n")
	
	tm = 0

	starting = True
	
	while tm < num_strings[chunk_no]: # this should actually not be needed if we read the pointers
		n = -1
		bit = 0
		x = 0
		
		if starting:
			outfile.write("[" + str(tm) + "]")
			if debug: outfile.write("  actual " + str(hex((r.totalread / 8) + base_offset + chunk_offset)) + ", table " + str(hex(offsets[tm] + 0x10 - 0x2000 + base_addresses[chunk_no])) + " ")
			outfile.write("\n")

			starting = False

		while not bit == 1: 
			bit = r.readbits(1)
			n += 1
			
		v = r.readbits(3)
		x = (n << 3) | v

		if x > 47:
			print "Warning: encountered unknown character", x, " -- ROM corrupt?"
			outfile.write("{" + str(x) + "}")
			continue
		
		if table[x] == 0x3F:
			# control character: insert item name
			outfile.write("<insert>")
			
			# for our purposes this means: skip to next whole byte, then read 2 bytes
			while not (r.totalread % 8) == 0:
				r.readbits(1) # skip to next whole byte
				
			outfile.write("<" + str(r.readbits(8)) + ">")
			outfile.write("<" + str(r.readbits(8)) + ">")
			continue
		
		if table[x] == 0x1C:
			# control character: clear screen
			outfile.write("<cls>\n")
			continue			

		if table[x] == 0x1D:
			# control character: line break
			outfile.write("<br>\n")
			continue			

		if table[x] == 0x1F:
			# control character: end of string
			outfile.write("<end>\n")
			
			while not (r.totalread % 8) == 0:
				r.readbits(1) # skip to next whole byte
			
			tm += 1	
			starting = True
			
			continue
		
		outfile.write(charset[table[x]])
	outfile.close()

print "Script dumped."
f.close()
