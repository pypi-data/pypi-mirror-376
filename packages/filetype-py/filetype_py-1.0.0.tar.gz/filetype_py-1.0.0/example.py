import file_type
import sys

if(len(sys.argv)) <= 1:
    print(sys.argv[0]+" <filetype>")
    exit(0)

# Get the file type information about the given file
file = file_type.filetype_from_file(sys.argv[1])

# Print what the file type is, as a human readable string
print("Name:", file.name())

# Print the ID of the file type, corresponding to the table at https://github.com/theseus-rs/file-type/blob/main/FILETYPES.md
print("ID:", file.id())

# Print the extension(s) that this file type usually has.
print("Extensions:", file.extensions())

# Print the 'source type' of the file. This is not very well documented in the original library, but I think it's the source of where the library got the extension?
print("Source Type:", file.source_type())
