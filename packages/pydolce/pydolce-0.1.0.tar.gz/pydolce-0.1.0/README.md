# Dolce

Because broken docs leave a bitter taste.

**Dolce** is a tool designed to streamline the process of managing and generating documentation/docstrings for your python projects.

## Installation

Comming soon...

## Usage


### Check command

- Check docstrings in all python files in the current directory and subdirectories

```bash
dolce check
```

- Check in specific directory (recursevly) or file

```bash
dolce check path/to/file_or_directory.py
```

- Check only documented code

```bash
dolce check --ignore-missing
```

- Sepecify local ollama model (default is `codestral`)

```bash
dolce check --model <model_name>
```

## To be implemented

- [ ] Support config in pyproject.toml for default options
- [ ] Support config for secret environment variables for LLM APIs
- [ ] Use third-party tools to check docstrings style, parameters, etc.
- [ ] Add cache system to avoid re-checking unchanged code

---

## 📦 For Developers

Make sure you have the following tools installed before working with the project:

* [**uv**](https://docs.astral.sh/uv/) → Python project and environment management
* [**make**](https://www.gnu.org/software/make/) → run common project tasks via the `Makefile`

### Getting Started

Install dependencies into a local virtual environment:

```bash
uv sync --all-groups
```

This will create a `.venv` folder and install everything declared in `pyproject.toml`.

Then, you can activate the environment manually depending on your shell/OS:

* **Linux / macOS (bash/zsh):**

  ```bash
  source .venv/bin/activate
  ```

* **Windows (PowerShell):**

  ```powershell
  .venv\Scripts\Activate.ps1
  ```

* **Windows (cmd.exe):**

  ```cmd
  .venv\Scripts\activate.bat
  ```

### Set up your environment variables  

Make a copy of the `.env.example` file and edit it with your settings:

```bash
cp .env.example .env
```

### Run dolce

```bash
make run
```

### Linting, Formatting, and Type Checking

```bash
make qa
```

Runs **Ruff** for linting and formatting, and **Mypy** for type checking.

### Running Unit Tests

Before running tests, override any required environment variables in the `.env.test` file.

```bash
make test
```

Executes the test suite using **Pytest**.

### Building the Project

```bash
make build
```

Generates a distribution package inside the `dist/` directory.

### Cleaning Up

```bash
make clean
```

Removes build artifacts, caches, and temporary files to keep your project directory clean.

### Building docs

```bash
make docs
```

Generates the project documentation inside the `dist/docs` folder.

When building the project (`make build`) the docs will also be generated automatically and
included in the distribution package.

## 🤝 Contributing

Contributions are welcome!
Please ensure all QA checks and tests pass before opening a pull request.

---

<sub>🚀 Project starter provided by [Cookie Pyrate](https://github.com/gvieralopez/cookie-pyrate)</sub>