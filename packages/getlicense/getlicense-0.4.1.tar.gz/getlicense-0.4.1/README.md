# GetLicense

![screenshot](./screenshot.png)

<p align="center"><em>📖 A tool to quickly generate software license files with customizable project details</em>
    <br>
    <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/ashkanfeyzollahi/getlicense">
    <img alt="GitHub License" src="https://img.shields.io/github/license/ashkanfeyzollahi/getlicense">
    <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/getlicense">
</p>

**getlicense** is a command-line tool that helps you easily choose and generate a license for your software project. It fetches license templates from an online repository, fills in basic project information (like organization name, project name, and copyright year), and saves the result as a LICENSE file. You can also cache templates for offline use and list available options directly from the terminal.

## Installation

1. **[Install Pipx](https://gist.github.com/ashkanfeyzollahi/7bbf36fb876a3781efbbb3ef841b5f4e)** (if you don't have it already)

2. **Install `getlicense` using Pipx**:

```bash
pipx install getlicense
```

## Usage

```plain
usage: getlicense [-h] [--individual INDIVIDUAL] [-L] [-l] [-n] [-c] [--organization ORGANIZATION] [-o OUTPUT] [--project PROJECT] [--year YEAR] [license_name]

A tool to quickly generate software license files with customizable project details

positional arguments:
  license_name          Name of license template to fetch (e.g., mit, gpl3 and etc.)

options:
  -h, --help            show this help message and exit
  --individual INDIVIDUAL
                        The name of the individual who holds the copyright to the software
  -L, --list-cached-templates
                        List cached license templates
  -l, --list-templates  List available license templates
  -n, --no-cache        Don't cache the license template file when downloaded
  -c, --offline         Get the cached license template instead of downloading
  --organization ORGANIZATION
                        The name of the organization that holds the copyright to the software
  -o, --output OUTPUT   Where to write the license template content to
  --project PROJECT     The name of the software project
  --year YEAR           The year of the software's copyright
```
