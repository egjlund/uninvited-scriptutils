# uninvited-scriptutils
Script insertion and extraction utilities for Uninvited (NES)

## What is this?
These are Python 2.x script dumping and insertion utilities for working with Uninvited, the NES game. I wrote these about five years ago (May-June 2016) while working on reverse-engineering the game for an English to Swedish translation I was working on.

These are weirdly written, somewhat specifically suited to Swedish, very poorly documented (you will have to read the awful mess of quick-and-dirty Python code in order to figure out what's happening and how to use them) and by now I've forgotten most of the finer technical details. There is little or no error checking in many parts. You need to edit the source to specify the filename. The programs do *work*, however. Maybe they will be fun to mess around with for someone.  

## How to use
* Name your ROM image ´uninvited.nes´ and place it in the same directory as the scripts. Make sure to make a backup of the stock ROM beforehand as we will be overwriting it.

* Run ´python uninvited-extract.py´. This will extract the stock script into three different text files, ´uninvited-dumpN.txt´.

* Edit the text files and save them as ´uninvited-dumpN-translated.txt´.

* Run ´python uninvited-insert.py´ to insert the edited script into the ROM. After this, if you have chosen to insert a new frequency table, *you will no longer be able to extract the script back from the ROM. The extractor only works with the stock frequency table for now.*

These are the bare basics. You will need to read and edit the code to do more interesting things like change the character set.

## Technical notes (incomplete)

These notes assume an American NTSC ROM with the 16-byte iNES header stripped. If your ROM image has a header, add 0x10 to each address referenced.

### General ROM layout   
Uninvited is a 256 kB (2 Mbit) game with 128 kB of PRG ROM and 128 kB of CHR ROM. For the purposes of this document, you can ignore CHR ROM (which starts at 0x20000) entirely.
   

### Object names   
The names of inventory items, spells, and interactive environment objects (such as cabinets that can be opened, etc.) are stored at 0xF000-0xF7FF (2048 bytes). This is the only uncompressed text in the game. Each character is 1 byte and refers to a tile number in the name table. For instance, B0 is 'A', B1 is 'B', and so forth.

There is a Thingy-compatible table file (uninv.tbl) which can be used with several popular hex editors to see and edit object names.

Each object name is 8 bytes long and padded with FF bytes if shorter. For instance, the inventory item 'COLOGNE' is stored, starting at 0xF1C0, as:

```
B3 BF BC BF B7 BE B5 FF 
C  O  L  O  G  N  E      
```	

### Script data format
   
As an initial exercise before attempting to dump and translate Uninvited, I wrote a script dumper for Shadowgate, thinking that it might serve as a useful exercise -- after all, Shadowgate is already available in Swedish, and comparing the two versions might prove fruitful.
   
As it turns out, that was a bit of a waste of time -- Uninvited uses a rather different text compression scheme than Shadowgate. Whereas Shadowgate uses a fixed character length of 5 bits for everything except a couple of special 8-bit control characters, thereby achieving upwards of 62.5% compression compared to full bytes, Uninvited is a bit more clever. 

It uses a Huffman encoding scheme, which enables the 8 most commonly used characters to be encoded using only 4 bits, which then increases to 5, 6 and so forth as rarity increases. This is pretty efficient since this means that for a lot of the text -- English, uppercase-only -- can be packed two letters per byte. 
   
However, the game has lots and lots of empty space in the script data chunks, padded with FF bytes and free for the taking, so why they even bothered coming up with a more advanced compression scheme -- that is just barely more effective than Shadowgate's 5-bit encoding -- is a valid question.

The characters in the game, ordered from most frequent to least (well, according to whatever analysis were made during development, at least,) are as follows:

| Index | Character |
|-------|-----------|
|    0 |  (space) |
|    1 |  E |
|    2 |  T |
|    3 |  O |
|    4 |  S |
|    5 |  A |
|    6 |  I |
|    7 |  N |
|    8 |  R |
|    9 |  H |
|   10 |  L |
|   11 |  U |
|   12 |  D |
|   13 |  (newline) |
|   14 |  Y |
|   15 |  . |
|   16 |  C |
|   17 |  M |
|   18 |  G |
|   19 |  (string termination) |
|   20 |  F |
|   21 |  P |
|   22 |  W |
|   23 |  B |
|   24 |  K |
|   25 |  ' |
|   26 |  V |
|   27 |  , |
|   28 |  (clear screen) |
|   29 |  " |
|   30 |  ! |
|   31 |  - |
|   32 |  X |
|   33 |  Z |
|   34 |  Q |
|   35 |  J |
|   36 |  ? |
|   37 |  _ |
|   38 |  : |
|   39 |  ( |
|   40 |  ) |
|   41 |  2 |
|   42 |  9 |
|   43 |  ; |
|   44 |  0 |
|   45 |  7 |
|   46 |  8 |
|   47 |  4 |
 

As you can tell, even though the character set allows for up to 64 characters, only 48 are ever used in the script. This doesn't mean that the corresponding character tiles are unused; for instance the digit '1' appears nowhere in the script yet is used in several item names.

Even though strings can consist of an arbitrary number of bits, and thus may stop in the middle of a byte, they always *start* at an even byte address, and therefore the start of each string is easily addressable.

Script data starts at 0xC000. Immediately at that address, there is a 512-byte chunk containing pointers to strings. Each pointer is 16 bits and little endian, so they need to be byte-swapped. For example, the first two bytes are 00 82. Swap the two bytes around, and it points to 0x8200.

There are pointer tables at:

0x8000
0xC000
0x16000 (0xC000 + 0xA000 -- so add 0xA000 to each pointer address)

The translation table starts at 0x1E42F.

The tile table starts at 0x1DC37.


## Licenses
WTFPL, except bitio.py which is under the GNU Free Documentation License v1.2.
