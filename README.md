# VS Code - Local History Parser

The [March 2022](https://code.visualstudio.com/updates/v1_66) release of VS Code provided a new feature called [Local history](https://code.visualstudio.com/updates/v1_66#_local-history). It provides a mechanism to *keep track of local file changes independent of source control*.

The idea behind this project is provide a way to locate and filter all snapshots created by the **Local history** feature. It was born out of the necessity to restore two days worth of files lost via a misplaced `rm -rf *`.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U git+https://github.com/rudisimo/vscode-local-history-parser/archive/refs/heads/main.zip
```

## Usage

Display help message:

```bash
lhp -h
```

## Notes

I would like to extend a HUGE thanks to the [Visual Studio Code](https://twitter.com/code/) team for the lifesaver feature.

Github Issues:

- [Add support for local history (microsoft/vscode#26339)](https://github.com/microsoft/vscode/issues/26339)
- [Test: Local History (microsoft/vscode#145461)](https://github.com/microsoft/vscode/issues/145461)

## License

Licensed under the [MIT](LICENSE.txt) license.