# litesurf <!-- omit in toc -->

A simple Python CLI tool to create a basic web browser.

![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
[![License](https://img.shields.io/github/license/bhatishan2003/litesurf)](LICENSE)
[![Python CI](https://github.com/bhatishan2003/litesurf/actions/workflows/python-app.yml/badge.svg)](https://github.com/bhatishan2003/litesurf/actions/workflows/python-app.yml)

## Table of Contents <!-- omit in toc -->

- [Installation](#installation)
  - [Create and activate a virtual environment:](#create-and-activate-a-virtual-environment)
- [Usage](#usage)
  - [Command Line Usage](#command-line-usage)
- [Building Standalone Executables with PyInstaller](#building-standalone-executables-with-pyinstaller)
  - [1. Install PyInstaller](#1-install-pyinstaller)

---

## Installation

-   Clone the repository:

    ```bash
    git clone https://github.com/bhatishan2003/litesurf
    cd litesurf
    ```

### Create and activate a virtual environment:

1. **Create a Virtual Environment [Optional, but recommended]**

    Run the following command to create a [virtual environment](https://docs.python.org/3/library/venv.html):

    ```bash
    python3 -m venv .venv
    ```

-   **Activate:**

    -   **Windows (PowerShell):**

        ```bash
        .venv\Scripts\activate
        ```

    -   **Linux/Mac (Bash):**

        ```bash
        source .venv/bin/activate
        ```

-   **Deactivate:**

    ```bash
    deactivate
    ```

-   **Install the package:**

    ```bash
    pip install .
    ```

-   **For development (editable mode):**

    ```bash
    pip install -e .
    ```

## Usage

### Command Line Usage

-   Following commands should be entered to get a pop-up browse.

    ```bash
    litesurf
    litesurf --file test.html
    ```

## Building Standalone Executables with PyInstaller

You can generate platform-specific standalone executables for your litesurf project using **PyInstaller**.

### 1. Install PyInstaller

```bash
pip install pyinstaller
```

-   **Windows**

    ```poweshell
    pyinstaller --name litesurf --onefile run_litesurf.py
    ```

-   **MacOS**

    ```bash
    pyinstaller --name litesurf --onefile --windowed run_litesurf.py
    ```

    -   Convert the .app into a .dmg for distribution:

        ```bash
        hdiutil create -volname litesurf -srcfolder dist/litesurf.app -ov -format UDZO litesurf.dmg
        ```

-   **Linux**

    -   You can create a cross-platform source distribution from Windows (or Linux):

        ```bash
        python setup.py sdist
        ```

    -   Linux users can install it via:
        ```bash
        pip install litesurf-0.0.1.tar.gz
        ```
