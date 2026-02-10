# List all available commands
_default:
    @just --list

# Install dependencies
@bootstrap:
    uv sync

# Run tests using pytest
@test *ARGS:
    uv run --group dev pytest {{ ARGS }}

# Build documentation using Sphinx
@docs-build LOCATION="docs/_build/html":
	uv run --group docs sphinx-build docs {{ LOCATION }}

# Serve documentation locally
@docs-serve:
	uv run --group docs sphinx-autobuild docs docs/_build/html --port 8001
