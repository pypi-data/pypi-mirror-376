from pathlib import Path
import sys
from typing import Any
from typing import Literal
from typing import TypedDict
from typing import get_args
from typing import get_origin
from typing import get_type_hints

from sphinx.application import Sphinx

package = Path(__file__).parents[2].resolve().joinpath("src", "ccu")
sys.path.append(str(package))

# -- General Sphinx Options ------------------------------------------------------
extensions = [
    "notfound.extension",
    "sphinx.ext.apidoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.duration",
    "sphinx.ext.extlinks",
    "sphinx.ext.ifconfig",
    "sphinx.ext.imgconverter",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_click",
    "sphinx_copybutton",
]
source_suffix = ".rst"
root_doc = "index"
project = "ccu"
version = release = "0.0.6"
author = "Ugochukwu Nwosu"
year = "2024"
copyright = f"{year}, {author}"
nitpicky = True
nitpick_ignore_regex = {
    ("py:.*", ".*(ttk|tkinter).*"),
    ("py:(class|obj)", r"ccu.fancyplots.validation\..*"),
    ("py:class", r"NDArray|np.floating"),
    ("py:class", "pydantic_settings.sources.base.PydanticBaseSettingsSource"),
    ("py:class", "DotenvType"),
    ("py:class", "CliSettingsSource"),
    ("py:class", "PathType"),
}
exclude_patterns = ["build"]
modindex_common_prefix = ["ccu."]
default_role = "code"
extlinks = {
    "issue": (
        "https://gitlab.com/ugognw/python-comp-chem-utils/-/issues/%s",
        "issue %s",
    ),
    "mr": (
        "https://gitlab.com/ugognw/python-comp-chem-utils/-/merge_requests/%s",
        "MR %s",
    ),
    "gitref": (
        "https://gitlab.com/ugognw/python-comp-chem-utils/-/commit/%s",
        "commit %s",
    ),
    "repo-file": (
        "https://gitlab.com/ugognw/python-comp-chem-utils/-/blob/main/%s",
        "`%s`",
    ),
}
linkcheck_ignore = [r"https://www.law-two.com"]
rst_epilog = r"""
.. |CO2RR| replace:: CO\ :sub:`2`\ RR
.. |H2| replace:: H\ :sub:`2`
.. |N2| replace:: N\ :sub:`2`
.. |H2O| replace:: H\ :sub:`2`\ O
.. |H2O2| replace:: H\ :sub:`2`\ O\ :sub:`2`
.. |NH3| replace:: NH\ :sub:`3`
.. |O2| replace:: O\ :sub:`2`
.. |NO2| replace:: NO\ :sub:`2`
.. |CH4| replace:: CH\ :sub:`4`
"""

# Options for LaTeX
latex_engine = "xelatex"

# -- Options for sphinx.ext.autodoc ------------------------------------------
autoclass_content = "both"


AutodocOptions = TypedDict(
    "AutodocOptions",
    {
        "inherited_members": bool,
        "undoc_members": bool,
        "show_inheritance": bool,
        "no-index": bool,
    },
)


def include_annotations(
    app: Sphinx,
    what: Literal[
        "module", "class", "exception", "function", "method", "attribute"
    ],
    name: str,
    obj: Any,
    options: AutodocOptions,
    lines: list[str],
) -> None:
    """Build annotations from :class:`.Annotated` metadata for TypedDicts.

    The docstring for such TypedDict subclasses must terminate with the line
    "Keys:".
    """
    # if not isinstance(obj, type) or not lines or lines[-1] != "Keys:":
    #     return
    if what != "class" or len(lines) < 2 or lines[-2].strip() != "Keys:":
        return

    type_hints = get_type_hints(obj, include_extras=True)

    for key, v in type_hints.items():
        annotations: list[str] = []
        origin = get_origin(v).__name__
        for annotation in get_args(v):
            if isinstance(annotation, str):
                annotations.append(annotation)
        description = " " + ". ".join(annotations)
        lines.insert(-1, f":param {key}: {description}")
        lines.insert(-1, f":type {key}: {origin}")


# -- Options for sphinx.ext.intersphinx --------------------------------------
intersphinx_mapping = {
    "ase": ("https://ase-lib.org/", None),
    "matplotlib": ("https://matplotlib.org/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pymatgen": ("https://pymatgen.org/", None),
    "python": ("https://docs.python.org/3", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "click": ("https://click.palletsprojects.com/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "pydantic_settings": (
        "https://docs.pydantic.dev/",
        "_inventory/pydantic_settings/objects.inv",
    ),
}

# -- Options for Napoleon ----------------------------------------------------
napoleon_google_docstring = True
napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_custom_sections = [("Keys", "Attributes")]

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"
html_logo = "_static/ccu.png"
html_static_path = ["_static"]
html_last_updated_fmt = "%a, %d %b %Y %H:%M:%S"
html_theme_options = {
    "source_repository": "https://gitlab.com/ugognw/python-comp-chem-utils/",
    "source_branch": "main",
    "source_directory": "docs/source",
    "dark_css_variables": {
        "color-brand-primary": "#e0ffef",
        "color-brand-content": "#e0ffef",
    },
}
pygments_style = "sphinx"
pygments_dark_style = "monokai"

gitlab_url = "https://gitlab.com/ugognw/python-comp-chem-utils"

smartquotes = True
html_split_index = False
html_short_title = f"{project}-{version}"


# -- Options for sphinx_copybutton -------------------------------------------
copybutton_exclude = ".linenos, .gp, .go"
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True

# -- Registering listeners
# def setup(app: Sphinx) -> None:
#     _ = app.connect("autodoc-process-docstring", include_annotations)
