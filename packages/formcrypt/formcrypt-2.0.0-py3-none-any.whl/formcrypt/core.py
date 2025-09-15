import random
import os

from formcrypt.utils import *
from formcrypt.sourcefile import SourceCode

FORMCRYPT_SOURCE = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), 'rsrc', 'formcrypt.c' )
FORMCRYPT_HEADER = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), 'rsrc', 'formcrypt.h' )

DEFAULT_KEY_SIZE = 16

class Rc4EncryptedString( object ):
    """
    Represents an encrypted buffer object, providing macro definitions for the ciphertext, key & buffer creation.

    :param: string
        The string to encrypt & hold in the buffer. Can be string or bytes.
    
    :param: keysize
        The size of the key to use for encrypting the string.

    :param: name
        A name for the nacro in the source code. This macro is used to access the ciphertext / key within the source code.
    """
    def __init__( self, string: str or bytes, keysize=DEFAULT_KEY_SIZE, name=f'FORMCRYPT_STRING_{str(random.randint(0,999))}' ):
        self.plaintext                  = string.decode() if isinstance(string, bytes) else string
        self.key                        = bytes( random.randint( 0, 0xFF ) for _ in range( keysize ) )
        self.ciphertext                 = rc4( self.key, self.plaintext.encode() )
        self.string_macro_definition    = f"# define { name.upper() } { to_c_byte_array_string( self.ciphertext ) }"
        self.key_macro_definition       = f"# define { name.upper() }_KEY { to_c_byte_array_string( self.key ) }"
        self.creation_macro             = f"NEW_BUFFER ({ name.lower() }, { name.upper() }, { name.upper() }_KEY )"

class FormCrypt( object ):
    """
    Represents the source for formcrypt.

    :param: strings
        A dicitionary of strings to encrypt & include in the formcrypt header. Syntax for dictionary
        is -> macro_name=string_value. 'macro_name' sets the name of the macro for string ciphertext
        in the header file & string is the data to encrypt.
    
    :param: keysize
        An int which sets the size of the default encryption key size for all string keys within the 
        formcrypt source. Default to 16 bytes.
    """
    def __init__(self, strings: dict, keysize = DEFAULT_KEY_SIZE):
        self.source = SourceCode(source_file=FORMCRYPT_SOURCE, filename='formcrypt.c')
        self.header = SourceCode(source_file=FORMCRYPT_HEADER, filename='formcrypt.h')
        for macro_name, string in strings.items():
            if not isinstance(macro_name, str) or macro_name == '':
                raise ValueError(f"Invalid macro name: expected non-empty string, got {type(macro_name).__name__} or empty string.")
            if not isinstance(string, str) or string == '':
                raise ValueError(f"Invalid string value: expected non-empty string, got {type(string).__name__} or empty string")
        for buf in [ Rc4EncryptedString( name=macro_name, string=string, keysize = keysize ) for macro_name, string in strings.items() ]:

            self.header.content += f"\n{ buf.string_macro_definition }\n{ buf.key_macro_definition }\n"
        self.header.replace_content(f'#define KEY_SIZE { keysize }', r'#define KEY_SIZE 8')

    def write_to_dir( self, outdir="", source_dir="", header_dir="" ):
        """ Write the source/header files to single or targeted directories """
        if outdir != "":
            if not os.path.exists( outdir ):
                raise FileNotFoundError(f"Could not find { outdir }")
            self.source.write_to_dir( outdir )
            self.header.write_to_dir( outdir )
        elif source_dir != "" and header_dir != "":
            if not os.path.exists( source_dir ) or not os.path.exists( header_dir ):
                raise FileNotFoundError(f"Could not locate source ({ source_dir }) AND OR ({ header_dir })")
            self.source.write_to_dir( source_dir )
            self.header.write_to_dir( header_dir )
        else:
            raise Exception("Must specify either outdir OR outidr AND header_dir. outdir will write both files to the same location.")
        return True