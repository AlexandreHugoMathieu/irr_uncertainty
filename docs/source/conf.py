# Configuration file for the Sphinx documentation builder.
import sys
import os

sys.path.insert(0, os.path.abspath('../..'))

# -- General configuration
project = 'irr_uncertainty'
copyright = '2025, Alexandre MATHIEU'
author = 'Alexandre MATHIEU'

# -- General configuration
extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

html_theme = 'sphinx_rtd_theme'
