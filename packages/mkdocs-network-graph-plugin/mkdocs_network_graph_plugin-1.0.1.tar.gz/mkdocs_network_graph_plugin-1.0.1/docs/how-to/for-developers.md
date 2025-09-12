# For Developers

If you want to contribute to the development of this plugin, this guide will help you get started.

## Requirements

Before you begin, make sure you have the following tools installed:

- [**Python**](https://www.python.org/)
- [**uv**](https://github.com/astral-sh/uv)
- [**Git**](https://git-scm.com/)

## Setting up the Development Environment

1. **Clone the repository and navigate into the directory:**

    ```bash
    git clone https://github.com/develmusa/mkdocs-network-graph-plugin.git
    cd mkdocs-network-graph-plugin
    ```

2. **Setup the development environment:**
    Run the following commands to set up your environment.

    First, sync your virtual environment with the project's dependencies:

    ```bash
    uv sync
    ```

    Next, install the required Python versions for testing:

    ```bash
    uv python install 3.10 3.11 3.12 3.13
    ```

    Install the project in editable mode, along with the development tools:

    ```bash
    uv pip install -e '.[dev]'
    ```

    Finally, install the pre-commit hooks:

    ```bash
    uv run pre-commit install
    ```

## Running the Documentation Site Locally

To preview the documentation and see your changes live, you'll need to run a local server.

1. **Start the local server:**

    ```bash
    uv run mkdocs serve
    ```

    You can now view the documentation at `http://127.0.0.1:8000/`. The server will automatically reload when you make changes.

## Running Tests

This project uses [**`nox`**](https://nox.thea.codes/) to run the test suite across multiple Python versions.

```bash
uv run nox -s tests
```

You can also run tests for your current Python environment using [**`pytest`**](https://docs.pytest.org/):

```bash
uv run pytest
```

## Code Style

This project uses [**`Ruff`**](https://docs.astral.sh/ruff/) for linting and formatting. You can run the `lint` session with `nox` to check and fix issues:

```bash
uv run nox -s lint
```

Alternatively, you can run `ruff` directly:

To check your code for errors:

```bash
uv run ruff check .
```

To automatically format your code:

```bash
uv run ruff format .
```

## Using Pre-Commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to automatically enforce code style and run checks before each commit. The hooks are installed when you set up the development environment.

With pre-commit installed, the defined checks will run on any staged files every time you run `git commit`. If a check fails, the commit will be aborted, allowing you to fix the issues before proceeding.

To update the pre-commit hooks to their latest versions, run:

```bash
uv run pre-commit autoupdate
```

!!! note
    The setup, documentation, testing and linting commands are also available as tasks in `.vscode/tasks.json` for Visual Studio Code users.

## Contribution Checklist

Before submitting a pull request, please ensure you have completed the following steps:

- [ ] Added your changes to the `CHANGELOG.md` file.
- [ ] Ensured all tests pass by running `uv run pytest`.
- [ ] Verified that all pre-commit hooks pass on your changes.

## See Also

- [Why Use a Graph?](../explanation/why-use-a-graph.md)
- [Configuration](../reference/configuration.md)
- [Customization](../how-to/customization.md)
