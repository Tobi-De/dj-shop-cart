# List all available commands
_default:
    @just --list

# Build documentation using Sphinx
@docs-build LOCATION="docs/_build/html":
    sphinx-build docs {{ LOCATION }}

# Install documentation dependencies
@docs-install:
    hatch run docs:python --version

# Serve documentation locally
@docs-serve:
    hatch run docs:sphinx-autobuild docs docs/_build/html --port 8001