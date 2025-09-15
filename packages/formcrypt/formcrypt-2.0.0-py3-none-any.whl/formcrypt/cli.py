import argparse
import os
import shutil
import traceback

from formcrypt.terminal import *
from formcrypt.core import *

def get_macro_string_pairs(args):
    """ convert key/value pair strings to dictionary object. """
    key_value_pairs = {}
    strings         = []
    if args.strings:
        strings = args.strings
    elif args.file:
        with open(args.file, 'r') as strings_input_file:
            strings = strings_input_file.read().splitlines()
    if strings == []:
        return None
    for arg in strings:
        if '=' in arg:
            key, value = arg.split('=', 1)
            key_value_pairs[key] = value
        else:
            raise ValueError(f"Invalid format for argument: {arg}. Use key=value.")
    return key_value_pairs

def get_args() -> argparse.Namespace:
    """ parse arguments from user """
    parser = argparse.ArgumentParser(description="FormCrypt v2.0.0. A tool for creating encrypted string buffers in C/C++. Encrypt your strings & insert the code files into your malware source.\n")
    input_data_arg_group = parser.add_mutually_exclusive_group()
    input_data_arg_group.add_argument('--strings', type=str, nargs="+", help='A list of strings to encrypt. Each item must be key/value pair seperated by equal sign (=). Key is name of macro for ciphertext, value is string to encrypt. Syntax -> MacroName=StringValue.')
    input_data_arg_group.add_argument('--file', type=str, help='path to a file containing each string to encrypt, seperated by new line. Each item must be key/value pair seperated by equal sign (=). Key is name of macro for ciphertext, value is string to encrypt. Syntax -> MacroName=StringValue.')
    parser.add_argument('--keysize', default=16, type=int, help='size of the encryption key for all encrypted buffers')
    parser.add_argument('--outdir', type=str, help='An alternative directory to write the source files to. Defaults to current directory. Cant be used with --source_dir or --header_dir', default=None)
    parser.add_argument('--source_dir', type=str, help='Write formcrypt.c to a specific directory (requires --header_dir)', default=None)
    parser.add_argument('--header_dir', type=str, help='Write formcrypt.h to a specific directory (requires --source_dir)', default=None)
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress the banner')
    return parser.parse_args()

def main():
    args = get_args()
    if args.outdir is None and args.source_dir is None and args.header_dir is None:
        args.outdir = "."
    elif args.outdir is not None and args.source_dir is not None and args.header_dir is not None:
        log_message("Must use --outdir OR --source_dir AND --header_dir. All three can't be used together.", 'error')
        exit()
    elif args.source_dir is None and args.header_dir is not None or args.source_dir is not None and args.header_dir is None:
        log_message(f"Failed to specify --{ 'source_dir' if args.source_dir is None else '--header_dir' }.", 'error')

    strings = get_macro_string_pairs( args )
    if strings is None:
        log_message("No strings were received. Quitting.")
        exit()

    try:
        formcrypt   = FormCrypt( strings=strings, keysize=args.keysize )
        if args.outdir is not None and os.path.exists( args.outdir ):
            if formcrypt.write_to_dir( outdir=args.outdir ):
                log_message( f'Wrote source files to { os.path.abspath(args.outdir) }' )
        else:
            if os.path.exists( args.source_dir ) and os.path.exists( args.header_dir ):
                if formcrypt.write_to_dir( source_dir=args.source_dir, header_dir=args.header_dir ):
                    log_message( f'Wrote { formcrypt.source.filename } to { os.path.abspath(formcrypt.source.path_on_disk) }' )
                    log_message( f'Wrote { formcrypt.header.filename } to { os.path.abspath(formcrypt.header.path_on_disk) }' )
                    
    except Exception as e:
        log_message(f"An error occurred while creating the formcrypt source code.\nError: {e}\n{traceback.format_exc()}", status='error')
    