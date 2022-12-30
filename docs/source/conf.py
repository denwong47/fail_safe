# -*- coding: utf-8 -*-
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath("../src/py"))

from fail_safe import config

config.env.SPHINX_IS_BUILDING = 1

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Fail Safe Context Manager"
copyright = "2022, Denny Wong Pui-chung, denwong47@hotmail.com"
author = "Denny Wong Pui-chung"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# napoleon for Numpy Docs
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = [
    "forestreet_cache/**",
]

autodoc_member_order = "bysource"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_css_files = ["sig_word-break.css"]
# html_logo = "https://forestreet.com/wp-content/themes/Forestreet/assets/img/logo.svg"
html_theme_options = {
    "icon_links": [
        {
            "name": "GitHub Repository",
            "url": "https://github.com/denwong47/fail_safe",
            "icon": "fab fa-github-square",
        },
        # {
        #     "name": "GitLab",
        #     "url": "https://gitlab.com/<your-org>/<your-repo>",
        #     "icon": "fab fa-gitlab",
        # },
        # {
        #     "name": "Twitter",
        #     "url": "https://twitter.com/<your-handle>",
        #     "icon": "fab fa-twitter-square",
        # },
    ],
    "favicons": [
        # {
        #     "rel": "icon",
        #     "sizes": "16x16",
        #     "href": "https://somewhere.com/favicon.ico",
        # },
        #   {
        #      "rel": "icon",
        #      "sizes": "32x32",
        #      "href": "favicon-32x32.png",
        #   },
        #   {
        #      "rel": "apple-touch-icon",
        #      "sizes": "180x180",
        #      "href": "apple-touch-icon-180x180.png"
        #   },
    ],
}
