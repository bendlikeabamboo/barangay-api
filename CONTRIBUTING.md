# Contributing to barangay-api

First off, thank you for considering contributing to `barangay-api`! It's people like you that make the open-source civic tech community such a great place.

This project is a FastAPI wrapper for the [`barangay`](https://pypi.org/project/barangay/) package, aimed at providing easy access to Philippine Standard Geographic Code (PSGC) data.

## 📜 Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## 🛠️ Development Setup

We use [`uv`](https://github.com/astral-sh/uv) for Python package and dependency management. It's extremely fast and provides a consistent environment.

### Prerequisites

- Python 3.12 or higher
- `uv` installed on your system ([Installation guide](https://docs.astral.sh/uv/getting-started/installation/))

### Setting up your environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bendlikeabamboo/barangay-api.git
   cd barangay-api
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   uv sync
   ```
   This will create a `.venv` directory and install all necessary dependencies including development tools.

3. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate  # On Linux/macOS
   # or
   .venv\Scripts\activate     # On Windows
   ```

4. **Set up pre-commit hooks:**
   We use `pre-commit` to ensure code quality (linting with `ruff`, type checking with `mypy`).
   ```bash
   uv run pre-commit install
   ```

## 🚀 How to Contribute

### Reporting Bugs

- Check the [GitHub Issues](https://github.com/bendlikeabamboo/barangay-api/issues) to see if the bug has already been reported.
- If not, open a new issue. Provide a clear description, steps to reproduce, and expected vs. actual behavior.

### Suggesting Enhancements

- Open a GitHub Issue with the "enhancement" label.
- Describe the feature you'd like to see and why it would be useful for the project.

### Pull Requests

1. **Fork the repository** and create your branch from `main`.
2. **Make your changes.** Ensure your code follows the project's style (enforced by `ruff`).
3. **Run tests.** (Add tests if you're adding new features!)
4. **Verify linting and types:**
   ```bash
   uv run ruff check .
   uv run mypy .
   ```
5. **Commit your changes.** Use clear and descriptive commit messages.
6. **Push to your fork** and submit a pull request to the `main` branch.

## 🏛️ Civic Tech Principles

As a civic tech project, we value:
- **Transparency:** Open data and open source.
- **Accessibility:** Ensuring the API is easy to use and well-documented.
- **Inclusivity:** Welcoming contributors from all backgrounds.

## 💬 Communication

If you have questions or want to discuss ideas, feel free to open an issue or start a discussion on GitHub.

---

Thank you for your contribution! 🇵🇭
