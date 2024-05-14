import math
import os
import sys

import cairo

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

class TreeView:

    """
    >>> tree_view = TreeView()
    >>> Directory.create_test_instance(size=3).populate_tree_view(tree_view)
    >>> w, h = 300, 400
    >>> x, y = 50, 50
    >>> surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    >>> context = cairo.Context(surface)
    >>> tree_view.paint(context, w, h, x, y, debug=True)
    >>> surface.write_to_png("tree_view_3.png")
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

    def add(self, name, weight=None):
        if weight is None:
            if self.indent in [0, 1]:
                weight = 2
            elif self.indent in [2]:
                weight = 1.2
            else:
                weight = 1
        self.items.append(TreeItem(self.indent, name, weight))

    def paint(self, context, width, height, x, mouse_y, debug=False):
        font_size = 20
        context.set_source_rgb(1, 1, 1)
        context.paint()
        if debug:
            size = 8
            context.rectangle(x-size, mouse_y-size, size*2, size*2)
            context.set_source_rgb(0.2, 0.2, 1)
            context.fill()
        context.set_font_size(font_size)
        ascent, descent, font_height, _, _ = context.font_extents()
        context.set_source_rgb(1, 0, 0)
        distribution = NormalDistribution(center=mouse_y, deviation=font_size*1.2)
        self.scale(
            item_size=font_height,
            container_size=height,
            distribution=distribution,
        )
        y = 0
        for item in self.items:
            y += item.paint(
                context=context,
                font_size=font_size,
                font_height=font_height,
                y=y,
                ascent=ascent,
                debug=debug
            )
        if debug:
            for point in range(0, height, 1):
                context.line_to(
                    distribution.at(point)*3000,
                    point
                )
            context.set_source_rgb(0.2, 1, 0.2)
            context.stroke()

    def scale(self, item_size, container_size, distribution=None):
        """
        Even:

        >>> tree_view = TreeView()
        >>> tree_view.add("one")
        >>> tree_view.add("two")

        >>> tree_view.scale(item_size=10, container_size=20)
        [1.0, 1.0]

        >>> tree_view.scale(item_size=10, container_size=10)
        [0.5, 0.5]

        Uneven:

        >>> tree_view = TreeView()
        >>> tree_view.add("one", 1)
        >>> tree_view.add("two", 2)

        >>> tree_view.scale(item_size=10, container_size=30)
        [1, 2]

        >>> tree_view.scale(item_size=10, container_size=15)
        [0.5, 1.0]
        """
        sum_item_sizes = 0
        for item in self.items:
            sum_item_sizes += item.calculate_size(item_size)
        if sum_item_sizes > container_size:
            scale = container_size / sum_item_sizes
        else:
            scale = 1
        for item in self.items:
            item.apply_scale(scale)
        return [item.scale for item in self.items]

class TreeItem:

    def __init__(self, indent, name, weight):
        self.indent = indent
        self.name = name
        self.weight = weight

    def calculate_size(self, item_size):
        return item_size * self.weight

    def apply_scale(self, scale):
        self.scale = scale * self.weight

    def paint(self, context, font_size, y, ascent, debug, font_height):
        context.set_font_size(font_size*self.scale)
        if debug:
            context.rectangle(
                10*self.indent,
                y,
                300,
                font_height*self.scale
            )
            context.stroke()
        context.move_to(10*self.indent, y+ascent*self.scale)
        context.text_path(self.name)
        context.fill()
        return font_height*self.scale

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
    def create_test_instance(cls, size=3):
        def make_tree(path, size):
            paths[path] = []
            for x in range(size):
                name = f"folder {x+1}"
                make_tree(os.path.join(path, name), size-1)
                paths[path].append(name)
            for x in range(size):
                paths[path].append(f"file {x+1}")
        paths = {}
        make_tree(".", size)
        return cls.create_null(paths=paths)

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
        self.queue_draw()

class NormalDistribution:

    def __init__(self, center, deviation):
        self.center = center
        self.deviation = deviation

    def max(self):
        return self.at(self.center)

    def at(self, x):
        """
        >>> x = NormalDistribution(center=0, deviation=1)

        >>> round(x.at(0), 2)
        0.4

        >>> round(x.at(2), 2)
        0.05
        """
        return (
            1 / math.sqrt(2*math.pi*self.deviation**2)
        ) * math.e ** (
            -0.5*((x-self.center)/self.deviation)**2
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
