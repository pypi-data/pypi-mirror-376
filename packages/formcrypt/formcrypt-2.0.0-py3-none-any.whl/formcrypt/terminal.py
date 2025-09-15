RED     = "\033[31m"
WHITE   = "\033[37m"
BOLD    = "\033[1m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
RESET   = "\033[0m"
MAGENTA = "	\033[35m"

BANNER  = f"""{MAGENTA}
____ ____ ____ _    ____ ____ _    ____ ____ 
|  _\\|   || . \\|\\/\\ | __\\| . \\||_/\\| . \\|_ _\\
| _\\ | . ||  <_|   \\| \\__|  <_| __/| __/  || 
|/   |___/|/\\_/|/v\\/|___/|/\\_/|/   |/     |/

             |‾|
            /‾‾‾\\  _________/‾‾‾\\
            | O | | __   ___  O  |
            \\___/ |_| |_|   \\___/

{RED}A string obfuscation tool for C/C++ malware.{RESET}

{WHITE}Author:  {YELLOW}wizardy0ga
{WHITE}Version: {YELLOW}2.0.0
{WHITE}Github:  {YELLOW}https://github.com/wizardy0ga/formcrypt
{RESET}            
"""

def highlight(text: str, _format: str) -> str:
    return (_format + text + RESET)

def log_message(text, status='ok'):
    match status:
        case 'ok':
            COLOR = GREEN
        case 'error':
            COLOR = RED
        case 'warn':
            COLOR = YELLOW

    print(f"{ BOLD + WHITE }==> {COLOR + text + RESET}")