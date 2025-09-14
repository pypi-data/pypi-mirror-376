class SourceType:
    Default = 0
    Httpd = 1
    Iana = 2
    Linguist = 3
    Pronom = 4
    Wikidata = 5


def filetype_from_file(path: str) -> FileType: 
    """Attempt to determine the FileType from a file path.

    Args:
        path: a path to the file you want to open

    Returns: A FileType object
    """
    pass

def filetype_from_bytes(bytes: bytes) -> FileType: 
    """Attempt to determine the FileType from a sequence of bytes.

    Args:
        bytes: A sequence of bytes that you want to examine

    Returns: A FileType object
    """
    pass

def filetype_from_media_type(media_type: str) -> list[FileType]: 
    """Get the file type information for a given media type. (i.e. 'image/png')

    Args:
        media_type: A str containing the media type

    Returns: A list of FileType objects
    """
    pass

def filetype_from_extension(extension: str) -> list[FileType]: 
    """Get the file types for a given extension.

    Args:
        extension: A str containing the extension (without the dot).

    Returns: A list of FileType objects
    """
    pass


class FileType:
    def id(self: FileType) -> int: 
        """Get the file type identifier. This is an integer that corresponds to the table at https://github.com/theseus-rs/file-type/blob/main/FILETYPES.md

        Args:
            self: A FileType object

        Returns: The file type identifier
        """
        pass

    def name(self: FileType) -> str: 
        """Get the human-readable name of the file type
            
        Args:
            self: A FileType object

        Returns: The file type's name
        """
        pass

    def source_type(self: FileType) -> SourceType:
        """Get the source for this file type. This is the source that provided the information the library uses to determine the file, i.e. ICANN or Wikidata.
    
        Args:
            self: A FileType object

        Returns: The file type's source types
        """
        pass

  
    def extensions(self: FileType) -> list[str]:
        """Get the file type extension(s)
        
        Args:
            self: A FileType object

        Returns: The file type's extensions
        """
        pass