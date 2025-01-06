from datetime import datetime
import os
import posixpath
import sys

local_extensions_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "exts")
)
if local_extensions_path not in sys.path:
    sys.path.append(local_extensions_path)

project = "ThingLab Blog"
author = "Alex Martens"
html_title = project  # sphinx appends "documentation" without this set

# Sphinx overwrites copyright year if SOURCE_DATE_EPOCH is set
# https://github.com/sphinx-doc/sphinx/blob/e17ed74fe027eb84aaf72ce92c4b1bd8ebf8c049/sphinx/config.py#L715-L743
os.environ.pop("SOURCE_DATE_EPOCH", None)


def current_year() -> int:
    nix_last_modified_date = os.getenv("NIX_LAST_MODIFIED_DATE")
    if nix_last_modified_date:
        last_modified_year = nix_last_modified_date[:4]
        if not last_modified_year.startswith("20"):
            raise ValueError(f"Unable to parse year from {nix_last_modified_date}")
        return int(last_modified_year)
    else:
        return datetime.now().year


copyright = f"2024-{current_year()}, {author}"

language = "en"

extensions = [
    "myst_parser",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx_blog",
    "sphinx_copybutton",
    "sphinx_favicon",
    "sphinx_sitemap",
    "sphinx_svgbob",
    "sphinxcontrib.spelling",
    "sphinxext.rediraffe",
]

nitpicky = True

###############################################################################
# HTML style
###############################################################################

pygments_dark_style = "monokai"

favicons = [
    "favicon.svg",
    {"rel": "mask-icon", "href": "favicon_mask.svg", "color": "#FFFFFF"},
]

html_static_path = ["_static"]

# by default page source will have ".txt" at the end, which isn't correct
html_sourcelink_suffix = ""
html_copy_source = False
html_show_sourcelink = False

html_baseurl = "https://thinglab.org"

html_theme = "furo"
html_theme_options = {
    "top_of_page_buttons": ["view"],
    "source_view_link": "https://github.com/newAM/blog/tree/main/content/{filename}",
    "footer_icons": [
        {
            "name": "RSS",
            "url": posixpath.join(html_baseurl, "atom.xml"),
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 448 512">
                    <!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.-->
                    <path fill-rule="evenodd" d="M0 64C0 46.3 14.3 32 32 32c229.8 0 416 186.2 416 416c0 17.7-14.3 32-32 32s-32-14.3-32-32C384 253.6 226.4 96 32 96C14.3 96 0 81.7 0 64zM0 416a64 64 0 1 1 128 0A64 64 0 1 1 0 416zM32 160c159.1 0 288 128.9 288 288c0 17.7-14.3 32-32 32s-32-14.3-32-32c0-123.7-100.3-224-224-224c-17.7 0-32-14.3-32-32s14.3-32 32-32z"/>
                </svg>
            """,
            "class": "",
        },
        {
            "name": "GitHub",
            "url": "https://github.com/newAM",
            # from Furo docs
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}

html_extra_path = ["robots.txt"]

###############################################################################
# Spelling
###############################################################################

spelling_lang = "en_US"
spelling_word_list_filename = "spelling_wordlist.txt"
# scans the repository with git, which isn't in a nix build
spelling_ignore_contributor_names = False

###############################################################################
# Redirects from previous zola blog.
# And previous ablog + pydata theme.
###############################################################################

rediraffe_redirects = {
    "blog/archive": "archive",
    "blog/category": "tags",
    "home-server-2024": "2024/12/home_server_2024",
    "nixos-router": "2024/12/nixos_router_hardware",
    "nixos-router-hardware": "2024/12/nixos_router_hardware",
    "nixos-router-software": "2024/12/nixos_router_software",
    "starting-a-blog": "2024/12/starting_a_blog",
}
