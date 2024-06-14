# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'dj-shop-cart'
copyright = '2024, Tobi DEGNON'
author = 'Tobi DEGNON'
release = '2022'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser", "sphinx_design"]
myst_enable_extensions = ["colon_fence"]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'shibuya'
html_static_path = ['_static']

html_theme_options = {
  "accent_color": "orange",
  "nav_links": [
        {
            "title": "Usage",
            "url": "usage"
        },
        {
            "title": "Contributing",
            "url": "contributing"
        },
        {
            "title": "Code of Conduct",
            "url": "codeofconduct"
        },
        {
            "title": "License",
            "url": "license"
        },
    ],
    "page_layout": "compact",
}
