import tkinter as tk
from tkinter import ttk, filedialog
import tkinter.font as tkfont
from html.parser import HTMLParser
import requests
from io import BytesIO
from PIL import Image, ImageTk
import dukpy
import re


class Node:
    def __init__(self, tag=None, attrs=None, parent=None, data=None):
        self.tag = tag  # None for text nodes
        self.attrs = dict(attrs or [])
        self.children = []
        self.parent = parent
        self.data = data  # for text nodes

    def append(self, node):
        self.children.append(node)
        node.parent = self

    def get_attr(self, name, default=None):
        return self.attrs.get(name, default)

    def __repr__(self):
        if self.tag:
            return f"<{self.tag} {self.attrs}>"
        return f"Text({self.data!r})"


# ---------------------- HTML -> DOM parser ----------------------
class SimpleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = Node("html")
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag=tag.lower(), attrs=attrs)
        self.current.append(node)
        # void elements: do not push to current
        voids = {"img", "br", "meta", "link", "input", "hr"}
        if tag.lower() not in voids:
            self.current = node

    def handle_endtag(self, tag):
        # move current up until matching tag
        t = tag.lower()
        node = self.current
        while node is not None and node.tag != t:
            node = node.parent
        if node is None:
            return
        self.current = node.parent or self.root

    def handle_data(self, data):
        txt = data.strip("\n")
        if not txt:
            return
        node = Node(tag=None, data=txt)
        self.current.append(node)


# ---------------------- Utilities ----------------------


def parse_style(style_str):
    styles = {}
    if not style_str:
        return styles
    pairs = [s.strip() for s in style_str.split(";") if s.strip()]
    for p in pairs:
        if ":" in p:
            k, v = p.split(":", 1)
            styles[k.strip()] = v.strip()
    return styles


# convert css-font-size-like strings to points
def parse_font_size(s):
    if not s:
        return None
    m = re.match(r"(\d+)(px|pt)?", s)
    if m:
        val = int(m.group(1))
        unit = m.group(2) or "px"
        if unit == "px":
            return max(8, int(val * 0.75))  # crude px -> pt
        return val
    return None


# ---------------------- Renderer ----------------------
class SimpleRenderer:
    def __init__(self, canvas, width, on_link_click):
        self.canvas = canvas
        self.width = width
        self.x = 10
        self.y = 10
        self.line_spacing = 4
        self.images = []  # keep references
        self.on_link_click = on_link_click

    def render(self, node):
        # traverse children
        for child in node.children:
            if child.tag is None:
                self.draw_text(child.data, {})
            elif child.tag in ("p", "div"):
                self.handle_block(child, default_font=12)
            elif child.tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                size_map = {"h1": 28, "h2": 22, "h3": 18, "h4": 16, "h5": 14, "h6": 12}
                size = size_map.get(child.tag, 12)
                self.handle_block(child, default_font=size, bold=True)
            elif child.tag == "img":
                self.draw_image(child)
            elif child.tag == "a":
                self.handle_link(child)
            elif child.tag == "br":
                self.newline(12)
            else:
                # generic: render children inline
                self.render(child)

    def handle_block(self, node, default_font=12, bold=False):
        styles = parse_style(node.get_attr("style", ""))
        font_size = parse_font_size(styles.get("font-size")) or default_font
        text = self.collect_text(node)
        if text:
            self.draw_text(text, {"font_size": font_size, "bold": bold, "align": styles.get("text-align")})
        # children like images might exist
        for c in node.children:
            if c.tag == "img":
                self.draw_image(c)
        self.newline(int(font_size * 0.6))

    def collect_text(self, node):
        parts = []
        for c in node.children:
            if c.tag is None:
                parts.append(c.data)
            elif c.tag == "a":
                # show link text inline
                parts.append(self.collect_text(c))
            else:
                parts.append(self.collect_text(c))
        return " ".join([p for p in parts if p])

    def draw_text(self, text, options):
        font_size = options.get("font_size", 12)
        bold = options.get("bold", False)
        align = options.get("align", "left")
        font_spec = ("Arial", int(font_size), "bold" if bold else "normal")
        # naive wrapping
        maxw = self.width - 20
        words = text.split()
        line = ""
        for w in words:
            test = (line + " " + w).strip()
            tw = tkfont.Font(family="Arial", size=int(font_size)).measure(test)
            if tw > maxw and line:
                self.canvas.create_text(self.x, self.y, anchor="nw", text=line, font=font_spec)
                self.y += int(font_size) + self.line_spacing
                line = w
            else:
                line = test
        if line:
            self.canvas.create_text(self.x, self.y, anchor="nw", text=line, font=font_spec)
            self.y += int(font_size) + self.line_spacing

    def draw_image(self, node):
        src = node.get_attr("src")
        if not src:
            return
        try:
            if src.startswith("http://") or src.startswith("https://"):
                resp = requests.get(src, timeout=10)
                img = Image.open(BytesIO(resp.content)).convert("RGBA")
            else:
                img = Image.open(src).convert("RGBA")
            # scale to fit
            maxw = self.width - 20
            w, h = img.size
            if w > maxw:
                ratio = maxw / w
                img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
            tkimg = ImageTk.PhotoImage(img)
            self.images.append(tkimg)
            self.canvas.create_image(self.x, self.y, anchor="nw", image=tkimg)
            self.y += img.size[1] + self.line_spacing
        except Exception as e:
            self.canvas.create_text(self.x, self.y, anchor="nw", text=f"[image failed: {e}]")
            self.y += 20

    def handle_link(self, node):
        href = node.get_attr("href")
        txt = self.collect_text(node) or href
        font_spec = ("Arial", 12, "underline")
        t_id = self.canvas.create_text(self.x, self.y, anchor="nw", text=txt, font=font_spec, tags=("link",))
        bbox = self.canvas.bbox(t_id)
        if bbox:
            x1, y1, x2, y2 = bbox
            rect_tag = f"linkrect{t_id}"
            # invisible rect to catch clicks
            rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline="", tags=(rect_tag,))

            # bind click
            def handler(event, href=href):
                self.on_link_click(href)

            self.canvas.tag_bind(rect_tag, "<Button-1>", handler)
        self.y += 18

    def newline(self, extra=10):
        self.y += extra


# ---------------------- JS Execution (very small surface) ----------------------
class JsSandbox:
    def __init__(self, set_title_callback):
        self.set_title = set_title_callback
        self.ctx = dukpy.JSInterpreter()

    def run(self, code):
        try:
            # Initialize basic JavaScript environment
            self.ctx.evaljs("""
                var console = {
                    log: function() {
                        var args = Array.prototype.slice.call(arguments);
                        print('[JS] ' + args.join(' '));
                    }
                };
                var document = { title: '' };
            """)

            # Execute the code
            result = self.ctx.evaljs(code)

            # Get the document title if it was set
            try:
                title = self.ctx.evaljs("document.title")
                if title:
                    self.set_title(title)
            except:
                pass

            return result
        except Exception as e:
            print("JS error:", e)
            return None


# ---------------------- Main Application ----------------------
class litesurf(tk.Tk):
    def __init__(self, start_url=None, start_file=None):
        super().__init__()
        self.title("litesurf")
        self.geometry("900x700")

        # top controls
        top = ttk.Frame(self)
        top.pack(side="top", fill="x")
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(top, textvariable=self.url_var)
        url_entry.pack(side="left", fill="x", expand=True, padx=4, pady=4)
        go = ttk.Button(top, text="Go", command=self.load_url)
        go.pack(side="left", padx=4)
        openbtn = ttk.Button(top, text="Open File", command=self.open_file)
        openbtn.pack(side="left", padx=4)

        # canvas with scrollbar
        self.canvas = tk.Canvas(self, bg="white")
        vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.canvas.config(scrollregion=self.canvas.bbox("all")))

        self.renderer = SimpleRenderer(self.canvas, width=860, on_link_click=self.on_link_click)
        self.js = JsSandbox(set_title_callback=self.set_title)

        # initial load if provided
        if start_url:
            self.url_var.set(start_url)
            # small delay not necessary; try to load immediately
            self.load_url()
        elif start_file:
            self.url_var.set(start_file)
            self.open_local(start_file)

    def set_title(self, t):
        self.title("litesurf - " + str(t))

    def clear(self):
        self.canvas.delete("all")
        self.renderer.y = 10
        self.renderer.images.clear()

    def on_link_click(self, href):
        # basic handling of relative/absolute
        if href.startswith("http://") or href.startswith("https://"):
            self.url_var.set(href)
            self.load_url()
        else:
            # maybe local file
            self.url_var.set(href)
            self.open_local(href)

    def open_local(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
            self.render_html(html)
        except Exception as e:
            self.clear()
            self.canvas.create_text(10, 10, anchor="nw", text=f"Failed to open {path}: {e}")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html;*.htm"), ("All files", "*.*")])
        if path:
            self.url_var.set(path)
            self.open_local(path)

    def load_url(self):
        url = self.url_var.get().strip()
        if not url:
            return
        try:
            if url.startswith("file://"):
                path = url[7:]
                self.open_local(path)
                return
            if url.startswith("http://") or url.startswith("https://"):
                resp = requests.get(url, timeout=10)
                html = resp.text
                self.render_html(html)
            else:
                # try as local file
                self.open_local(url)
        except Exception as e:
            self.clear()
            self.canvas.create_text(10, 10, anchor="nw", text=f"Failed to load {url}: {e}")

    def render_html(self, html):
        self.clear()
        parser = SimpleHTMLParser()
        parser.feed(html)
        # run scripts first (very naive): execute inline <script> text
        script_texts = []

        def collect_scripts(node):
            if node.tag == "script":
                # get text children
                s = " ".join([c.data for c in node.children if c.tag is None])
                script_texts.append(s)
            for c in node.children:
                collect_scripts(c)

        collect_scripts(parser.root)
        for s in script_texts:
            self.js.run(s)
        # render body
        body = None
        for c in parser.root.children:
            if c.tag == "body":
                body = c
                break
        if body is None:
            body = parser.root
        self.renderer.render(body)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))


def main(start_url=None, start_file=None):
    app = litesurf(start_url=start_url, start_file=start_file)
    app.mainloop()


if __name__ == "__main__":
    main()
