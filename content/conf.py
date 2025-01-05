from datetime import datetime
import os
import posixpath

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
    "ablog",
    "myst_parser",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_favicon",
    "sphinx_sitemap",
    "sphinxcontrib.spelling",
    "sphinxcontrib.svgbob",
    "sphinxext.rediraffe",
]

nitpicky = True

###############################################################################
# HTML style
###############################################################################

favicons = [
    "favicon.svg",
    {"rel": "mask-icon", "href": "favicon_mask.svg", "color": "#FFFFFF"},
]

html_static_path = ["_static"]

# by default page source will have ".txt" at the end, which isn't correct
html_sourcelink_suffix = ""
html_show_sourcelink = False

html_baseurl = "https://thinglab.org"

html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "use_edit_page_button": True,
    "footer_start": ["copyright"],
    "footer_end": [],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/newAM",
            "icon": "fa-brands fa-github",
        },
        {
            "name": "ThingLab Blog Atom Feed",
            "url": posixpath.join(html_baseurl, "blog", "atom.xml"),
            "icon": "fa-solid fa-rss",
        },
    ],
}

html_context = {
    "github_user": "newAM",
    "github_repo": "blog",
    "github_version": "main",
    "doc_path": "content",
}

html_sidebars = {
    "**": [
        # From pydata-sphinx-theme
        # https://github.com/pydata/pydata-sphinx-theme/blob/9b92ec9e8b834c303b842700acac47c7ef07aad9/src/pydata_sphinx_theme/theme/pydata_sphinx_theme/theme.conf#L7
        "sidebar-nav-bs.html",
        # Ablog sidebars
        "ablog/postcard.html",
        "ablog/recentposts.html",
        "ablog/categories.html",
        "ablog/archives.html",
    ]
}

html_extra_path = ["robots.txt"]

###############################################################################
# Blog
###############################################################################

post_date_format = "%Y-%m-%d"
post_date_format_short = post_date_format

###############################################################################
# Feeds
###############################################################################

blog_baseurl = html_baseurl
blog_feed_subtitle = (
    "Alex Martens' personal blog. A mix of software, firmware, and hardware projects."
)
blog_feed_fulltext = True
blog_archive_titles = True
# generate feeds in the root
blog_feed_templates = {
    # Use defaults, no templates
    "atom": {},
}

###############################################################################
# Spelling
###############################################################################

spelling_lang = "en_US"
spelling_word_list_filename = "spelling_wordlist.txt"
# scans the repository with git, which isn't in a nix build
spelling_ignore_contributor_names = False

###############################################################################
# Redirects from previous zola blog
###############################################################################

rediraffe_redirects = {
    "archive": "blog/archive",
    "tags": "blog/category",
    "home-server-2024": "2024/12/home_server_2024",
    "nixos-router-hardware": "2024/12/nixos_router_hardware",
    "nixos-router-software": "2024/12/nixos_router_software",
    "starting-a-blog": "2024/12/starting_a_blog",
    # handled with a symlink during build
    # "atom.xml": "blog/atom.xml",
}
