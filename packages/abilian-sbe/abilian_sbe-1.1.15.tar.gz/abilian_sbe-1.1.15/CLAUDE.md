# CLAUDE.md

This file provides guidance to LLMs when working with code in this repository.

## Project Overview

Abilian SBE (Social Business Engine) is a Flask-based social business platform for collaborative enterprise applications and enterprise social networks. The project follows a monorepo structure with Python backend and JavaScript/Vue.js frontend components.

## Key Architecture

- **Backend**: Flask application built on Abilian Core (Flask + SQLAlchemy)
- **Database**: PostgreSQL (production), SQLite (development/testing)
- **Task Queue**: Dramatiq with Redis backend
- **Frontend**: Vue.js 3 with Vite (in `front/` directory)
- **Assets**: Tailwind CSS for styling, managed through multiple build systems
- **Package Management**: UV for Python dependencies, npm/yarn for JavaScript

### Core Structure

- `src/abilian/` - Main Python package
  - `core/` - Core framework components (models, extensions, dramatiq)
  - `sbe/` - Social Business Engine apps and features
  - `web/` - Web layer components (forms, admin, uploads, etc.)
- `front/` - Vue.js frontend application
- `tailwind/` - Tailwind CSS configuration and assets
- `tests/` - Test suite
- `migrations/` - Database migration scripts

## Development Commands

### Environment Setup
```bash
# Install dependencies
make install
# or manually:
uv sync
pre-commit install
yarn

# Activate environment
uv run $SHELL
```

### Running the Application
```bash
# Development server (uses honcho + Procfile.dev)
make run

# Manual Flask server
flask run

# Frontend development
cd front && npm run dev
```

### Database Management
```bash
# Initialize database
flask db initdb

# Create admin user
flask createuser admin <email> <username>

# Run migrations
flask db upgrade
```

### Testing
```bash
# Run tests
make test
# or: pytest tests

# Run tests with coverage
make test-with-coverage

# Run long/slow tests
make test-long

# Test assets build
make test-assets

# Run tests with nox (multiple Python versions)
nox -s pytest
```

### Code Quality
```bash
# Run all linting
make lint

# Individual linters
make lint-ruff    # ruff check src tests
make lint-py      # flake8 src tests
make lint-mypy    # mypy --show-error-codes src tests
make lint-pyright # pyright src tests

# Formatting
make format       # ruff format + markdown-toc
```

### Frontend Commands
```bash
cd front/
npm run dev    # development server
npm run build  # production build
npx eslint src # lint JavaScript/Vue
npx prettier -c src # check formatting
```

## Environment Variables

Development configuration (put in `.env` file):
```bash
FLASK_SECRET_KEY=<your-secret-key>
FLASK_SQLALCHEMY_DATABASE_URI=postgres://localhost/sbe-demo
FLASK_SERVER_NAME=127.0.0.1:5000
FLASK_DEBUG=true
FLASK_MAIL_DEBUG=1
FLASK_REDIS_URI=redis://localhost:6379/0
FLASK_DRAMATIQ_BROKER_URL=redis://localhost:6379/0
```

## Important Notes

- The project uses UV for Python dependency management instead of pip/poetry
- Assets are built through Flask-Assets for backend templates and Vite for frontend
- Redis is required for task queue functionality
- External dependencies: PostgreSQL, ImageMagick, Poppler, LibreOffice, Java (for Closure compiler)
- Pre-commit hooks are configured and should be installed
- The codebase supports Python 3.11-3.13

## Testing Strategy

- Main test suite in `tests/` directory using pytest
- Database tests can run with different backends (SQLite, PostgreSQL)
- Asset compilation tests verify JavaScript/CSS build process
- Use `RUN_SLOW_TESTS=True` environment variable for comprehensive testing
- HTML validation tests available with `VALIDATOR_URL` configuration


# General Coding Conventions

## 1. Core Development Philosophy

These overarching principles guide our approach to building software.

*   **Simplicity and Readability**: Write simple, straightforward code that is easy to understand and maintain. Prioritize clarity over cleverness.
*   **No Duplication (DRY)**: Don't repeat yourself. Every piece of knowledge should have a single, unambiguous representation.
*   **Reveals Intention**: Use expressive names and small, focused functions to make the code's purpose clear.
*   **Minimalism**: Keep the design minimal by removing unnecessary code, classes, and complexity. Less code means less debt.
*   **Single Responsibility**: Ensure functions and classes have a single, well-defined purpose.
*   **Functional Core, Imperative Shell**: Isolate side-effects (like I/O and state changes) at the application's edges. Keep the core logic pure, immutable, and predictable.
*   **Performance**: Consider performance without sacrificing readability.

Adopt the 4 Rules of Simple Design:

- **Passes all tests:** First, ensure the code is correct and works as proven by a comprehensive test suite.
- **Reveals intention:** Write expressive code that is clear and easy to understand through good naming and small functions.
- **No duplication:** Eliminate redundancy by ensuring every piece of knowledge has a single, unambiguous representation (DRY).
- **Fewest elements:** Keep the design minimal by removing any unnecessary code, classes, or complexity.

## 2. Code Organization & Architecture

*   **Project Structure**: For larger projects, use a `src` directory to keep import paths clean.
    ```
    my_project/
    ├── docs/
    ├── src/
    │   └── my_project/
    │       ├── __init__.py
    │       ├── main.py
    │       └── utils.py
    ├── tests/
    ├── pyproject.toml
    └── README.md
    ```
*   **Onion Architecture**: For complex applications, separate concerns into distinct layers (Domain, Application, Infrastructure, Presentation) to promote loose coupling and high cohesion.
*   **Function Ordering**: In each module, define main functions and classes at the top (top-down), unless constrained otherwise.

## 3. Coding Best Practices

### Style and Formatting

*   **PEP 8**: Adhere to PEP 8 for naming conventions:
    *   `snake_case` for functions, variables, and modules.
    *   `PascalCase` for classes.
    *   `UPPER_SNAKE_CASE` for constants.
*   **Line Length**: Maximum of 88 characters.
*   **F-strings**: Use f-strings for string formatting, but not for logging.
*   **Descriptive Names**: Use clear and meaningful names for variables and functions (e.g., prefix handlers with "handle").

### Functional and Imperative Code

*   **Immutability**: Prefer immutable data structures like `tuples` and `frozenset`. Instead of modifying a collection in place, create a new one.
*   **Small, Pure Functions**: Write small, deterministic functions with clear inputs and outputs, avoiding side effects.
*   **Avoid Modifying Parameters**: Do not modify objects passed as parameters unless that is the function's explicit purpose.
*   **Early Returns**: Use early returns to reduce nested conditional logic.

### Comments and Documentation

*   **Docstrings**: All public APIs (modules, functions, classes, and methods) must have docstrings following PEP 257 conventions.
*   **Explain the "Why"**: Use comments to explain the reasoning behind non-obvious code, not to describe *what* the code does.
*   **TODO Comments**: Mark issues in existing code with a `TODO:` prefix.

### Error Handling

*   **Be Specific**: Catch specific exceptions rather than using a bare `except:`.
*   **Custom Exceptions**: Define custom exception classes for application-specific errors.
*   **Exception Chaining**: Use `raise NewException from original_exception` to preserve the original traceback.
*   **Avoid Exceptions for Control Flow**: Exceptions should be for exceptional circumstances, not normal program flow.

### Other Best Practices

*   **Avoid Magic Values**: Use named constants instead of hardcoded strings or numbers.
*   **Build Iteratively**: Start with minimal functionality, verify it works, and then add complexity.
*   **Clean Logic**: Keep core logic clean and push implementation details to the edges.

## 4. Python-Specific Guidelines

### Type Hinting

*   **Mandatory Type Hints**: Type hints are required for all function signatures to improve clarity and enable static analysis.
*   **Modern Syntax**: Prefer built-in generic types (e.g., `list[str]`) over aliases from the `typing` module (e.g., `List[str]`).
*   **Optional Types**: Use `X | None` for values that can be `None` and perform explicit `None` checks.

### Dependencies and Data Structures

*   **HTTP Requests**: Prefer `httpx` over `requests`.
*   **Data Structures**:
    *   Use `tuples` for heterogeneous, immutable data.
    *   Use `lists` for homogeneous, mutable data.
    *   Use `sets` for unordered collections of unique elements.

## 5. Tooling and Workflow

### Package Management

*   **Use `uv` exclusively**:
    *   **Installation**: `uv add <package>`
    *   **Running tools**: `uv run <tool>`
    *   **Forbidden**: Do not use `uv pip install` or the `@latest` syntax.

### Code Quality and Formatting

*   **Ruff**: Use `ruff` for formatting, linting, and import sorting.
    *   **Format**: `uv run ruff format .`
    *   **Check and Fix**: `uv run ruff check . --fix`
*   **Type Checking**: Use `pyrefly` for static type checking.
    *   **Run**: `uv run pyrefly`
*   **Pre-commit**: A `.pre-commit-config.yaml` is configured to run tools like Ruff and Prettier on every commit.

### Testing

*   **Framework**: Use `pytest`. Tests are located in the `tests/` directory.
    *   **Run tests**: `uv run pytest`
*   **Test Coverage**:
    *   New features require tests.
    *   Bug fixes require regression tests.
    *   Ensure edge cases and error conditions are tested.
*   **Test Philosophy**:
    *   **Avoid Mocks**: Prefer stubs. Whenever possible, verify a tangible outcome (state) rather than an internal interaction (behavior).
    *   **Realistic Inputs**: Test your code with realistic inputs and validate the outputs.

### Git Workflow

*   **Feature Branches**: Always work on feature branches, never commit directly to `main`.
    *   **Branch Naming**: Use descriptive names like `fix/auth-timeout` or `feat/api-pagination`.
*   **Atomic Commits**: Each commit should represent a single logical change.
*   **Conventional Commits**: Use the conventional commit style: `type(scope): short description`.
    *   Examples: `feat(eval): add new metrics`, `fix(cli): correct help message`.
*   **Commit Message Content**: Never include `co-authored-by` or mention the tool used to create the commit message.
* **Squash on Merge**: The original guidelines specified to squash commits only when merging to main. This strategy maintains a clean, linear history on the main branch while preserving the detailed, incremental history on feature branches during development and review.

### Error Resolution

1. Common Issues
   - Type errors:
     - Get full line context
     - Check Optional types
     - Add type narrowing
     - Verify function signatures
   - Line length:
     - Break strings with parentheses
     - Multi-line function calls
     - Split imports
   - Types:
     - Add None checks
     - Narrow string types
     - Match existing patterns

2. Best Practices
   - Check git status before commits
   - Run formatters before type checks
   - Keep changes minimal
   - Follow existing patterns
   - Document public APIs
   - Test thoroughly
