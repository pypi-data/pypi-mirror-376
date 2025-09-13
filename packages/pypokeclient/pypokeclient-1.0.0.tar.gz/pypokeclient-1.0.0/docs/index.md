<div align="center">
    <h1>PyPokéClient</h1>
    <img src="logo.png" width=35% /><br>
    <strong>Synchronous and asynchronous clients to fetch data from PokéAPI</strong><br><br>
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
    <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white">
</div>


---

## Features
!!! info "PyPI"
    The package is not present on PyPI at the moment, please follow the installation instrunctions in the respective section.

**PyPokéClient** is a Python wrapper for fetching data from PokéAPI, its main features are:

- **Coverage:** all PokéAPI endpoints are covered.
- **Data validation:** uses Pydantic dataclasses for the API implementation.
- **Flexibility:** can choose between synchronous and asynchronous clients.
- **Caching:** can employ a local cache system for faster responses and to respect PokéAPI Fair Use policy.

---

## Installation
!!! warning "Requirements"
    This package requires :simple-python: >= 3.12.

It is highly advised to create a new virtual environment.
=== ":simple-uv: uv"
    ```console
    $ uv venv
    ```
=== ":simple-python: pip"
    ```console
    $ python -m venv .venv
    ```

!!! note
    When using the default virtual environment name (i.e.: _.venv_), uv will automatically find and use the virtual environment during subsequent invocations.

Then, activate the virtual environment
=== ":material-linux: Linux"
    ```console
    $ source .venv/bin/activate
    ```
=== ":material-microsoft-windows: cmd"
    ```console
    > .\.venv\Scripts\activate.bat
    ```
=== ":material-powershell: PowerShell"
    ```console
    > .\.venv\Scripts\Activate.ps1
    ```

You can now install the package by simply
=== ":simple-uv: uv"
    ```console
    $ uv pip install git+https://github.com/RistoAle97/pokeapi-python-wrapper
    ```
=== ":simple-python: pip"
    ```console
    $ pip install git+https://github.com/RistoAle97/pokeapi-python-wrapper
    ```
