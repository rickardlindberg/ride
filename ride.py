import os

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
        self.items.append((self.indent, name))

    def render(self):
        for indent, name in self.items:
            if indent > 0:
                print(f"{'--'*indent} {name}")
            else:
                print(name)

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

    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.add_events(
            self.get_events() |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        self.connect("draw", self.on_draw)
        self.connect("motion-notify-event", self.on_motion_notify_event)

    def on_draw(self, widget, context):
        context.set_source_rgb(1, 0, 0)
        context.rectangle(10, 10, 10, 10)
        context.fill()

    def on_motion_notify_event(self, widget, event):
        print(event)

if __name__ == "__main__":
    window = Gtk.Window()
    window.connect("destroy", Gtk.main_quit)
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    box.pack_start(Canvas(), True, True, 0)
    window.add(box)
    window.show_all()
    Gtk.main()
