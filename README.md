# Dan's Toolbox

Just a bunch of Python CLI tools.

## Installation

First install the [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager.

```bash
# This will add the `toolbox` CLI command.
uv tool install git+https://github.com/dangffn/python-toolbox
```

### Development Installation

```bash
git clone https://github.com/dangffn/python-toolbox && cd python-toolbox
uv venv --python 3.12 --seed
source .venv/bin/activate
uv sync --group dev

# Test with coverage.
uv run pytest --cov=toolbox
```

# Usage

```bash
> toolbox --help
usage: toolbox [-h] [-v] {net,image,video} ...

A bunch of commands and stuff

positional arguments:
  {net,image,video}
    net              Network related utilities
    image            Image related utilities
    video            Video related utilities

options:
  -h, --help         show this help message and exit
  -v, --version      show program's version number and exit
```