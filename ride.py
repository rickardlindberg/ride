import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

class Canvas(Gtk.DrawingArea):

    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.connect("draw", self.on_draw)

    def on_draw(self, widget, context):
        context.set_source_rgb(1, 0, 0)
        context.rectangle(10, 10, 10, 10)
        context.fill()

if __name__ == "__main__":
    window = Gtk.Window()
    window.connect("destroy", Gtk.main_quit)
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    box.pack_start(Canvas(), True, True, 0)
    window.add(box)
    window.show_all()
    Gtk.main()
