from colorama import Fore, Style, init

# Initialize on import (Windows support)
init(autoreset=True)

# Semantic color constants
OK = Fore.GREEN + Style.BRIGHT  # success
INFO = Fore.CYAN + Style.NORMAL  # informational
WARN = Fore.YELLOW + Style.BRIGHT  # warnings
ERR = Fore.RED + Style.BRIGHT  # errors
RESET = Style.RESET_ALL  # reset
