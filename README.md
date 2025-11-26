# Dan's Toolbox

Just a bunch of Python CLI tools.

# Installation

First install the [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager.

```bash
# This will add the `toolbox` CLI command.
uv tool install git+https://github.com/dangffn/python-toolbox
```

Development installation.

```bash
git clone https://github.com/dangffn/python-toolbox && cd python-toolbox
uv venv --python 3.12 --seed
source .venv/bin/activate
uv sync --group dev

# Test.
python -m pytest
```

# Usage

```bash
toolbox --help
```