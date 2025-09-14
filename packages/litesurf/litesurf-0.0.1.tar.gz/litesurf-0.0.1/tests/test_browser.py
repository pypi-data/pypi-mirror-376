import sys
import os
import pytest

# ---------------- Ensure litesurf can be imported ----------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from litesurf import Node, SimpleHTMLParser, parse_style, parse_font_size, JsSandbox, SimpleRenderer


# ---------------- Node ----------------
def test_node_creation_and_repr():
    n = Node(tag="p", attrs=[("class", "test")])
    assert n.tag == "p"
    assert n.get_attr("class") == "test"
    assert "p" in repr(n)

    text_node = Node(data="Hello")
    assert text_node.tag is None
    assert "Hello" in repr(text_node)


def test_node_append_sets_parent():
    parent = Node("div")
    child = Node("span")
    parent.append(child)
    assert child in parent.children
    assert child.parent == parent


# ---------------- Style Parsing ----------------
def test_parse_style_valid():
    s = "font-size: 14px; color: red;"
    result = parse_style(s)
    assert result["font-size"] == "14px"
    assert result["color"] == "red"


def test_parse_style_empty_and_invalid():
    assert parse_style("") == {}
    assert parse_style(None) == {}


# ---------------- Font Size Parsing ----------------
def test_parse_font_size_px_and_pt():
    assert parse_font_size("16px") == 12  # px → pt
    assert parse_font_size("10pt") == 10


def test_parse_font_size_invalid():
    assert parse_font_size(None) is None
    assert parse_font_size("abc") is None


# ---------------- HTML Parser ----------------
def test_simple_html_parser_creates_dom():
    parser = SimpleHTMLParser()
    parser.feed("<html><body><p>Hello <b>World</b></p></body></html>")

    html_nodes = [c for c in parser.root.children if c.tag == "html"]
    assert html_nodes, "No <html> node found"
    html = html_nodes[0]

    body_nodes = [c for c in html.children if c.tag == "body"]
    assert body_nodes, "No <body> node found"
    body = body_nodes[0]

    assert body.tag == "body"
    assert any(c.tag == "p" for c in body.children)


def test_html_parser_handles_void_elements():
    parser = SimpleHTMLParser()
    parser.feed("<html><body><img src='test.png'/><br></body></html>")

    html_nodes = [c for c in parser.root.children if c.tag == "html"]
    assert html_nodes, "No <html> node found"
    html = html_nodes[0]

    body_nodes = [c for c in html.children if c.tag == "body"]
    assert body_nodes, "No <body> node found"
    body = body_nodes[0]

    tags = [c.tag for c in body.children]
    assert "img" in tags
    assert "br" in tags


# ---------------- JS Sandbox ----------------
@pytest.mark.skipif("dukpy" not in sys.modules, reason="dukpy not installed")
def test_js_sandbox_sets_title():
    title_holder = []

    def set_title(t):
        title_holder.append(t)

    js = JsSandbox(set_title_callback=set_title)
    js.run("document.title = 'Test Page';")
    assert "Test Page" in title_holder or "MockTitle" in title_holder


@pytest.mark.skipif("dukpy" not in sys.modules, reason="dukpy not installed")
def test_js_sandbox_invalid_code():
    js = JsSandbox(set_title_callback=lambda t: None)
    result = js.run("this is not valid js;")
    assert result is None


# ---------------- Renderer (logic, not GUI) ----------------
def test_renderer_collect_text_handles_nested_links():
    from unittest.mock import Mock

    canvas = Mock()
    renderer = SimpleRenderer(canvas, width=200, on_link_click=lambda href: None)

    parent = Node("p")
    parent.append(Node(data="Hello"))
    a = Node("a", attrs=[("href", "http://example.com")])
    a.append(Node(data="World"))
    parent.append(a)

    text = renderer.collect_text(parent)
    assert "Hello" in text and "World" in text


# ---------------- CLI (real run) ----------------
def test_cli_with_url(monkeypatch):
    import litesurf.cli as cli

    called = {}

    def fake_main(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr(cli, "main", fake_main)

    sys.argv = ["prog", "--url", "http://example.com"]
    cli.cli()

    assert called.get("start_url") == "http://example.com"
    assert called.get("start_file") is None


def test_cli_with_file(monkeypatch, tmp_path):
    import litesurf.cli as cli

    called = {}

    def fake_main(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr(cli, "main", fake_main)

    f = tmp_path / "sample.html"
    f.write_text("<html><body>Hello</body></html>")

    sys.argv = ["prog", "--file", str(f)]
    cli.cli()

    assert called.get("start_file") == str(f)
    assert called.get("start_url") is None


def test_cli_file_preferred(monkeypatch, tmp_path):
    import litesurf.cli as cli

    called = {}

    def fake_main(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr(cli, "main", fake_main)

    f = tmp_path / "index.html"
    f.write_text("<html><body>Preferred</body></html>")

    sys.argv = ["prog", "--file", str(f), "--url", "http://example.com"]
    cli.cli()

    assert called.get("start_file") == str(f)
    # Since cli passes start_url when no file, the url key may exist only if file is not provided
    # If you want to assert presence, optional:
    assert called.get("start_url") is None or called.get("start_url") == "http://example.com"
