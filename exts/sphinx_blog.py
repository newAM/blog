from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective, nodes
from sphinx.util.nodes import set_source_info
from sphinx.addnodes import document
from typing import Any, List, Dict
from datetime import datetime
from feedgen.feed import FeedGenerator
import os
from dateutil import tz
import posixpath


def _split(a: str) -> List[str]:
    return [s.strip() for s in (a or "").split(",")]


class BlogPostNode(nodes.Element):
    pass


class BlogPostDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        "tags": _split,
        "category": _split,
        "updated": lambda a: a.strip(),
        "title": lambda a: a.strip(),
    }

    def run(self):
        node = BlogPostNode()
        node.document = self.state.document
        set_source_info(self, node)
        self.state.nested_parse(self.content, self.content_offset, node, match_titles=1)
        node["date"] = self.arguments[0] if self.arguments else None
        node["tags"] = self.options.get("tags", [])
        node["category"] = self.options.get("category", [])
        node["title"] = self.options.get("title", None)
        node["updated"] = self.options.get("updated", None)
        return [node]


class BlogRecentNode(nodes.Element):
    pass


class BlogRecentDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        node = BlogRecentNode()
        node.document = self.state.document
        set_source_info(self, node)
        return [node]


class BlogArchiveNode(nodes.Element):
    pass


class BlogArchiveDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        node = BlogArchiveNode()
        node.document = self.state.document
        set_source_info(self, node)
        return [node]


class BlogTagsNode(nodes.Element):
    pass


class BlogTagsDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        node = BlogTagsNode()
        node.document = self.state.document
        set_source_info(self, node)
        return [node]


def top_level_heading(node: nodes.Node, doctree: nodes.document) -> str:
    for title in doctree.findall(nodes.title):
        return title.astext()
    raise Exception("No top level heading found for the given node")


def create_tag_reference(tag: str):
    ref_target = "tag-" + tag.lower()
    reference_node = nodes.reference(
        refuri="/tags/#" + ref_target,
        reftarget=ref_target,
        internal=True,
        anchorname=ref_target,
    )
    text_node = nodes.Text(tag)
    reference_node.append(text_node)
    return reference_node


def process_blog_posts(app: Sphinx, doctree: document):
    if not hasattr(app.builder.env, "blog_posts"):
        app.builder.env.blog_posts = {}

    docname: str = app.builder.env.docname

    # silence "WARNING: document isn't included in any toctree"
    app.env.metadata[docname]["orphan"] = True

    for node in doctree.findall(BlogPostNode):
        date_pretty = node["date"]

        updated = None
        if node["updated"] is not None:
            updated = datetime.strptime(node["updated"], "%Y-%m-%d")

        app.builder.env.blog_posts[docname] = {
            "title": top_level_heading(node, doctree),
            "tags": node["tags"],
            "category": node["category"],
            "date": datetime.strptime(date_pretty, "%Y-%m-%d"),
            "url": posixpath.join(
                "https://thinglab.org",
                app.builder.get_relative_uri(app.config.master_doc, docname),
            ),
            "updated": updated,
        }
        blog_metadata = nodes.container()
        paragraph = nodes.paragraph()
        paragraph.append(nodes.Text("Date: " + date_pretty))
        blog_metadata.append(paragraph)
        if len(node["tags"]):
            paragraph = nodes.paragraph()
            paragraph.append(nodes.Text("Tags: "))
            first = True
            for tag in node["tags"]:
                if not first:
                    paragraph.append(nodes.Text(", "))
                first = False
                paragraph.append(create_tag_reference(tag))
            blog_metadata.append(paragraph)
        blog_metadata.append(nodes.transition())
        node.replace_self(blog_metadata)


def post_bullet_list_item(
    app: Sphinx, docname: str, post_docname: str, post_data: Dict[str, Any]
) -> nodes.list_item:
    ref = nodes.reference()
    ref["refuri"] = app.builder.get_relative_uri(from_=docname, to=post_docname)
    ref.append(nodes.Text(post_data["title"]))

    paragraph = nodes.paragraph()
    date_pretty: str = post_data["date"].strftime("%Y-%m-%d")
    paragraph.append(nodes.Text(date_pretty + " "))
    paragraph.append(ref)

    post = nodes.list_item()
    post.append(paragraph)

    return post


def process_blog_recent(app: Sphinx, doctree: document, docname: str):
    """Replace `BlogRecentNode` nodes with lists of posts."""
    for node in doctree.findall(BlogRecentNode):
        recent_posts = nodes.bullet_list()
        for post_docname, post_data in sorted(
            app.builder.env.blog_posts.items(),
            key=lambda item: item[1]["date"],
            reverse=True,
        ):
            recent_post = post_bullet_list_item(app, docname, post_docname, post_data)
            recent_posts.append(recent_post)
        node.replace_self(recent_posts)


def process_blog_archive(app: Sphinx, doctree: document, docname: str):
    """Replace `BlogArchiveNode` nodes with an archive."""
    for node in doctree.findall(BlogArchiveNode):
        blog_archive = nodes.container()

        year = None
        year_list = None

        for post_docname, post_data in sorted(
            app.builder.env.blog_posts.items(),
            key=lambda item: item[1]["date"],
            reverse=True,
        ):
            post_date = post_data["date"]
            post_year = post_date.year

            if year != post_year:
                if year_list is not None:
                    year_section = nodes.section(ids=[f"year-{year}"])
                    year_section.append(nodes.title(text=str(year)))
                    year_section.append(year_list)
                    blog_archive.append(year_section)

                year = post_year
                year_list = nodes.bullet_list()

            post_item = post_bullet_list_item(app, docname, post_docname, post_data)
            year_list.append(post_item)

        year_section = nodes.section(ids=[f"year-{year}"])
        year_section.append(nodes.title(text=str(year)))
        year_section.append(year_list)
        blog_archive.append(year_section)

        node.replace_self(blog_archive)


def process_blog_tags(app: Sphinx, doctree: document, docname: str):
    """Replace `BlogTagsNode` nodes with tags."""
    for node in doctree.findall(BlogTagsNode):
        blog_tags = nodes.container()

        tags = {}

        for post_docname, post_data in sorted(
            app.builder.env.blog_posts.items(),
            key=lambda item: item[1]["date"],
            reverse=True,
        ):
            for tag in post_data["tags"]:
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append(
                    post_bullet_list_item(app, docname, post_docname, post_data)
                )

        for tag, tagged_posts in tags.items():
            tag_section = nodes.section(ids=[f"tag-{tag.lower()}"])
            tag_section.append(nodes.title(text=str(tag)))
            tag_list = nodes.bullet_list()
            for item in tagged_posts:
                tag_list.append(item)
            tag_section.append(tag_list)
            blog_tags.append(tag_section)

        node.replace_self(blog_tags)


def create_feed(app: Sphinx):
    feed = FeedGenerator()
    feed.id("https://thinglab.org")
    feed.title("ThingLab Blog")
    feed.author({"name": "Alex Martens"})
    feed.subtitle(
        "Alex Martens' personal blog. A mix of software, firmware, and hardware projects."
    )
    feed.copyright(app.builder.env.config.copyright)
    feed.language("en")
    feed.link(href="https://thinglab.org")
    feed.link(href="https://thinglab.org/atom.xml", rel="self")

    newest_date = None

    for post_docname, post_data in sorted(
        app.builder.env.blog_posts.items(),
        key=lambda item: item[1]["date"],
    ):
        feed_entry = feed.add_entry()
        feed_entry.id(post_data["url"])
        feed_entry.link(href=post_data["url"])
        feed_entry.title(post_data["title"])
        published = post_data["date"].replace(tzinfo=tz.gettz("America/Vancouver"))
        feed_entry.published(published)
        if newest_date is None:
            newest_date = published
        if published > newest_date:
            newest_date = published
        if post_data["updated"] is not None:
            updated = post_data["updated"].replace(tzinfo=tz.gettz("America/Vancouver"))
            print(f"set updated for {post_docname} to {updated}")
            if updated > newest_date:
                newest_date = updated
            feed_entry.updated(updated)
        else:
            feed_entry.updated(published)

    feed.updated(newest_date)

    out_path = os.path.join(app.builder.outdir, "atom.xml")
    feed.atom_file(out_path)

    if 0:
        yield


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_directive("blogpost", BlogPostDirective)
    app.add_directive("blogrecent", BlogRecentDirective)
    app.add_directive("blogarchive", BlogArchiveDirective)
    app.add_directive("blogtags", BlogTagsDirective)
    app.connect("doctree-read", process_blog_posts)
    app.connect("doctree-resolved", process_blog_recent)
    app.connect("doctree-resolved", process_blog_archive)
    app.connect("doctree-resolved", process_blog_tags)
    app.connect("html-collect-pages", create_feed)

    return {
        "version": "1.0.0",
        "parallel_read_safe": False,
        "parallel_write_safe": True,
    }
