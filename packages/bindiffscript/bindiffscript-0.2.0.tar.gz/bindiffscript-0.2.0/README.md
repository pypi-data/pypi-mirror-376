# bindiffscript

Fancy diff tool for reverse engineering binary files using a scripted approach.


## Install and use

You can either install `bindiffscript` via `pipx`

```bash
# have pipx installed first
pipx install bindiffscript
bindiffscript ...
```

.. simply run it via `uvx` provided by the `uv` package
```bash
# have uv installed first
uvx bindiffscript ...
```

.. or checkout the project and run it via `uv run`
```bash
# have git and uv installed first
git clone https://github.com/frans-fuerst/bindiffscript.git
cd bindiffscript
uv run bindiffscript ...
```

With all approaches you get an entry point `bindiffscript` with the
following syntax:
```bash
bindiffscript [<opts>..] <FILE>*
```

Since `<FILE>` can be a YAML file containing options and files to diff, you
can set a shebang to `bindiffscript` and make it executable:

```
#!/usr/bin/env bindiffscript
files:
    - path: path/to/file1.txt
    - path: path/to/file2.txt
```

.. which is the same as running `bindiffscript example.yaml`.

See the `examples` folder for syntax and inspiration!



## Contribution

### Initialize

```bash
git clone https://github.com/frans-fuerst/bindiffscript.git
cd bindiffscript
uv run pre-commit install
```

### Manually run checks and fixes

```bash
# run all checks which would be executed on commit, but on unstaged stuff, too
uv run pre-commit run --hook-stage pre-commit --all-files
# run all type checking (mypy) on current (unstaged) state
uv run pre-commit run check-python-typing --all-files
uv run pre-commit run check-python-linting --all-files
uv run pre-commit run check-python-format --all-files
uv run pre-commit run check-python-isort --all-files
uv run pre-commit run check-python-unittest --all-files
uv run pre-commit run check-python-doctest --all-files
uv run pre-commit run check-yaml-linting --all-files

uv run pre-commit run fix-python-linting --hook-stage manual --all-files
uv run pre-commit run fix-python-format --hook-stage manual --all-files
uv run pre-commit run fix-python-isort --hook-stage manual --all-files
```

implement -> `uv run pytest` -> commit -> repeat

### Manually run checks and fixes

```bash
uv version --bump <patch|minor|major>
uv build
# manual tests
git push
uv publish --token <TOKEN>
```

## Wishlist

- [x] Readme
- [x] Make width configurable via `width` attribute or command line option
- [x] Allow to specify padding value
- [x] Clip long files via `head`
- [ ] Configure cell format
- [ ] Show some sort of line number
- [ ] Skip identical lines
- [ ] Update on change
- [ ] Bash completion
- [ ] Show multiple files
- [ ] Highlight special/magic content
- [ ] Show hex/text side by side
- [ ] Scroll
- [ ] Show padding differently
- [ ] Auto-generate padding
- [ ] Padding: set to fixed position
- [ ] Padding: insert arbitrary data
- [ ] Padding: length from macro
- [ ] Annotations


## External Sources

* [A slightly less naive binary diff ](https://dev.to/taikedz/a-slightly-less-naive-binary-diff-294i)
* [dhex](https://www.dettus.net/dhex/)
