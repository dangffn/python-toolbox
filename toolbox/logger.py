"""Logger module providing convenience console instances using Rich."""

from rich import console as rich_console

console = rich_console.Console() # stdout
console_err = rich_console.Console(stderr=True) # stderr
