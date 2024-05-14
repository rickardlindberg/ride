import os
import sys

import cairo

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

class TreeView:

    """
    >>> tree_view = TreeView()
    >>> Directory.create_null(paths={
    ...     ".": ["folder1", "file2"],
    ...     "./folder1": ["file11"],
    ... }).populate_tree_view(tree_view)

    >>> tree_view.render()
    .
    -- folder1
    ---- file11
    -- file2

    >>> surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10)
    >>> context = cairo.Context(surface)
    >>> tree_view.paint(context, 10, 10, 0, 0)
    """

    def __init__(self):
        self.items = []
        self.indent = 0

    def begin_tree(self, directory):
        self.add(directory.name())
        self.indent += 1

    def leaf(self, file):
        self.add(file.name())

    def end_tree(self, directory):
        self.indent -= 1

    def add(self, name):
        self.items.append(TreeItem(self.indent, name))

    def render(self):
        for item in self.items:
            if item.indent > 0:
                print(f"{'--'*item.indent} {item.name}")
            else:
                print(item.name)

    def paint(self, context, width, height, x, y, debug=False):
        context.set_font_size(17)
        ascent, descent, font_height, _, _ = context.font_extents()
        context.set_source_rgb(1, 0, 0)
        scale = min(1, height/sum(item.weight*font_height for item in self.items))
        context.set_font_size(17*scale)
        y = 0
        for item in self.items:
            if debug:
                context.rectangle(
                    10*item.indent,
                    y,
                    300,
                    font_height*scale
                )
                context.stroke()
            context.move_to(10*item.indent, y+ascent*scale)
            context.text_path(item.name)
            context.fill()
            y += font_height*scale

    def scales(self, size, height):
        """
        >>> tree_view = TreeView()
        >>> tree_view.add("one")
        >>> tree_view.add("two")

        >>> tree_view.scales(size=10, height=20)
        [1, 1]

        >>> tree_view.scales(size=10, height=10)
        [0.5, 0.5]
        """
        total_height = 0
        for item in self.items:
            total_height += size
        if total_height > height:
            scale = height / total_height
        else:
            scale = 1
        return [scale for item in self.items]

class TreeItem:

    def __init__(self, indent, name):
        self.indent = indent
        self.name = name
        self.weight = 1
        self.scale = 1

class Directory:

    """
    >>> d = Directory.create_null()

    >>> d
    Directory(path='.')

    >>> d.children()
    [Directory(path='./folder1'), File(path='./file1')]

    >>> isinstance(Directory.create().children(), list)
    True
    """

    @classmethod
    def create(cls, path="."):
        return cls(os=os, path=path)

    @classmethod
    def create_null(cls, paths={".": ["folder1", "file1"]}):
        class NullPath:
            def isdir(self, path):
                return "folder" in path
        class NullOs:
            path = NullPath()
            def listdir(self, path):
                return paths.get(path, [])
        return cls(os=NullOs(), path=".")

    def __init__(self, os, path):
        self.os = os
        self.path = path

    def name(self):
        return os.path.basename(self.path)

    def children(self):
        def factory(path):
            if self.os.path.isdir(path):
                return Directory(os=self.os, path=path)
            else:
                return File(path)
        return [
            factory(os.path.join(self.path, x))
            for x in self.os.listdir(self.path)
        ]

    def populate_tree_view(self, tree_view):
        tree_view.begin_tree(self)
        for child in self.children():
            child.populate_tree_view(tree_view)
        tree_view.end_tree(self)

    def __repr__(self):
        return f"Directory(path={self.path!r})"

class File:

    def __init__(self, path):
        self.path = path

    def name(self):
        return os.path.basename(self.path)

    def populate_tree_view(self, tree_view):
        tree_view.leaf(self)

    def __repr__(self):
        return f"File(path={self.path!r})"

class Canvas(Gtk.DrawingArea):

    def __init__(self, directory):
        Gtk.DrawingArea.__init__(self)
        self.directory = directory
        self.add_events(
            self.get_events() |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        self.connect("draw", self.on_draw)
        self.connect("motion-notify-event", self.on_motion_notify_event)
        self.x = 0
        self.y = 0

    def on_draw(self, widget, context):
        view = TreeView()
        self.directory.populate_tree_view(view)
        view.paint(
            context,
            widget.get_allocated_width(),
            widget.get_allocated_height(),
            self.x,
            self.y,
            debug=os.environ.get("DEBUG", False)
        )

    def on_motion_notify_event(self, widget, event):
        self.x, self.y = self.translate_coordinates(
            self,
            event.x,
            event.y
        )

if __name__ == "__main__":
    window = Gtk.Window()
    window.connect("destroy", Gtk.main_quit)
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    box.pack_start(Canvas(Directory.create(
        path=(sys.argv[1:]+["."])[0]
    )), True, True, 0)
    window.add(box)
    window.show_all()
    Gtk.main()
