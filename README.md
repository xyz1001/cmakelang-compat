# cmakelang-compat

[![CI](https://github.com/xyz1001/cmakelang-compat/actions/workflows/ci.yml/badge.svg)](https://github.com/xyz1001/cmakelang-compat/actions/workflows/ci.yml)

Keep using **cmake-format 0.6.13 with Python 3.15**, without changing your
formatter command, CMake files, or `.cmake-format.yaml`.

This small, independent compatibility package fixes this lexer error in
`cmake-format` and `cmake-lint`:

```text
ValueError: Cannot use capturing groups in re.Scanner
```

It does not replace cmakelang, modify Python's standard library, or install a
different formatter. It targets **cmakelang 0.6.13** and activates only on affected
Python 3.15+ runtimes. Older Python versions keep their original behavior.

## Quick start

Install the patch **with the Python interpreter that runs your formatter**:

```sh
python -m pip install "cmakelang-compat==0.1.0a1"
cmake-format --check CMakeLists.txt
```

The example pins the initial pre-release. If it is not on PyPI yet, use the
[local wheel instructions](#install-from-source) instead. cmakelang itself must
already be installed; the patch deliberately does not install it as a dependency.

Start a new formatter process after installation. No project configuration
change is needed for a directly installed formatter.

## pre-commit

pre-commit normally creates its own isolated environment. Installing the patch
into your system Python does not install it into that environment.

Add the patch to the hook's additional dependencies:

```yaml
- repo: https://github.com/cheshirekow/cmake-format-precommit
  rev: v0.6.13
  hooks:
    - id: cmake-format
      additional_dependencies:
        - pyyaml
        - cmakelang-compat==0.1.0a1
```

For local testing before publication, replace the package requirement with a
wheel requirement such as `cmakelang-compat @ file:///D:/wheelhouse/cmakelang_compat-0.1.0a1-py3-none-any.whl`.
Do not commit a machine-specific wheel path to shared configuration.

## Neovim / Mason

Mason's package is named **`cmakelang`**, although the executable is
`cmake-format`. Install into that package's environment. For the default Windows
Mason location:

```powershell
& "$env:LOCALAPPDATA\nvim-data\mason\packages\cmakelang\venv\Scripts\python.exe" `
    -m pip install "cmakelang-compat==0.1.0a1"
```

For the default Linux/macOS location:

```sh
~/.local/share/nvim/mason/packages/cmakelang/venv/bin/python \
    -m pip install "cmakelang-compat==0.1.0a1"
```

Adapt the path when using a custom Mason installation root. Reinstalling or
updating the Mason package may recreate its environment and remove the patch.
If desired, arrange a single Neovim-level post-install step rather than changing
each CMake project.

Some Mason installations create environments with
`include-system-site-packages = true`. In that case the patch can instead be
installed into the **actual base interpreter** whose site-packages the
environment inherits. Check `venv/pyvenv.cfg` first; this is not guaranteed for
every environment. This also exposes the startup registration to other Python
processes using that base installation. Recheck after changing or upgrading the
base Python. If both environments contain the patch, the virtual environment's
copy normally takes precedence: upgrading only the global copy may not change
the version your formatter loads.

## Troubleshooting

- **The same error remains:** check which Python runs the formatter. A package
  installed globally may not be visible inside a virtual environment.
- **Check automatic startup on Python 3.15:** run the following with that exact
  interpreter. The first command should print `True`; the second shows the
  loaded package location.

  ```sh
  python -c "import sys; print('cmakelang_compat' in sys.modules)"
  python -c "import cmakelang_compat; print(cmakelang_compat.__file__)"
  ```

- **`--version` works but formatting fails:** version output does not exercise
  the lexer. Test an actual file with `cmake-format --check CMakeLists.txt`.
- **Startup is disabled:** `python -S` and embedded interpreters that skip
  normal `site` initialization do not load the patch automatically.
- **Another error or cmakelang version:** this is a targeted compatibility fix,
  not a general cmakelang upgrade. [Open an issue](https://github.com/xyz1001/cmakelang-compat/issues)
  with your traceback, Python version, and installation method.

## Uninstall

Use the same interpreter used for installation:

```console
python -m pip uninstall cmakelang-compat
```

New Python processes will no longer load the patch. Already-running processes
retain their imported modules until they exit.

## Install from source

Clone the repository and build a wheel with [uv](https://docs.astral.sh/uv/):

```sh
git clone https://github.com/xyz1001/cmakelang-compat.git
cd cmakelang-compat
uv build
python -m pip install ./dist/cmakelang_compat-0.1.0a1-py3-none-any.whl
```

Use the formatter's interpreter for the installation command. Install only a
trusted wheel: this package registers code at Python startup.

## How it works

A Python 3.15 `.start` file registers a lazy import hook. When cmakelang's lexer
is imported, it receives a module-local `re` proxy whose scanner matches the
original rules individually, retaining capturing groups and backreferences.
Other `re` functionality and the process-wide `re.Scanner` are unchanged.

No CMake code is reformatted on installation. Validate your own files before
wider deployment; matching the existing configuration alone does not prove
identical output for every possible input.

## Development

Install `.[test]` into a development environment, then run:

```sh
python -m unittest discover -s tests -v
```

CI builds distributions and tests the installed wheel, including automatic
startup, across its configured Python/OS matrix. Maintainers can find the PyPI
setup and release procedure in [RELEASING.md](https://github.com/xyz1001/cmakelang-compat/blob/main/RELEASING.md).

## License

GPL-3.0-only. See [LICENSE](https://github.com/xyz1001/cmakelang-compat/blob/main/LICENSE). cmakelang itself is a separate GPLv3
project; this package does not vendor its implementation.
