import os
import re

class SourceCode( object ):
    """
    Represents the source code of a file. Intended to be used as a parent object for other source code objects.

    Attributes:
        filename: string        -> The name of the file to write when writing to disk
        path_on_disk: string    -> The path of the file after it was written to disk
        launguage: string       -> The scripting or programming language associated with the source code
        comment_regex: list     -> A list of regex expressions for possible comments to be removed from the source code
        source_file: string     -> A path to a file on disk to use as the source code. Contents are only read, not modified.
        header_content: string  -> A string containing the base comment banner to use at the top of the source code.
        content: string         -> The contents of the source code
    """
    def __init__ ( self, filename: str, source_file = "" ):
        self.filename       = filename
        self.path_on_disk   = ""
        self.language       = ""
        self.comment_regex  = []
        self.source_file    = source_file
        self.header_content = f""
        
        if self.source_file != "":
            with open( self.source_file, 'r' ) as file:
                self.content = file.read()
    
    def replace_content( self, new_content: str, pattern: str, count = 1 ) -> None:
        """ Replace the content of a file via regex matching """
        self.content    = re.sub( pattern = pattern, repl = new_content, string = self.content, count = count )

    def write_to_dir( self, directory: str ) -> None:
        """ Write the source file to a directory """
        if not os.path.isdir( directory ):
            raise Exception( f"{ directory } is not a valid directory on the file system" )
        self.path_on_disk = os.path.join( directory, self.filename )
        with open( self.path_on_disk, 'w' ) as file:
            file.write( self.content )
        self.path_on_disk = self.path_on_disk
            
    def remove_comments( self ) -> None:
        """ Remove comments from the source code. """
        for pattern in self.comment_regex:
            self.replace_content( new_content = '', pattern = pattern, count = 0 )
    
    def remove_blank_lines( self ) -> str:
        """ Remove all blank lines greater than 2 from source """
        self.replace_content( new_content = '\n', pattern = r'(?m)(?:^[ \t]*\r?\n){2,}', count = 0 )

    def insert_header( self, additional_content = "" ) -> str:
        """ Insert a comment block at the top of the file, describing the file """
        match self.language:
            case 'asm':
                header = ";\n"
                for line in self.header_content.splitlines():
                    header += f"; { line }\n"
                for line in additional_content.splitlines():
                    header += f"; { line }\n"
                header += ";\n"
            case 'c':
                header = "/*\n"
                for line in self.header_content.splitlines():
                    header += f" * { line }\n"
                for line in additional_content.splitlines():
                    header += f" * { line }\n"
                header += "*/\n"

        header += self.content
        self.content = header