import json
import pathlib

import gi
gi.require_versions({
    'Gdk': '3.0',
    'Gtk': '3.0',
})
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this


class ProfileChooserWindow(Gtk.Window):
    def __init__(self, completion_callback):
        self.completion_callback = completion_callback
        self.mru_filename = pathlib.Path.home() / '.picave.mru'
        if self.mru_filename.exists():
            self.mru = json.load(self.mru_filename.open())
        else:
            self.mru = []
        Gtk.Window.__init__(self, title='Pi Cave profile chooser')
        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        layout.set_homogeneous(False)
        layout.set_spacing(4)
        self.listbox = Gtk.ListBox()
        for displayname, _ in self.mru:
            self.add_listbox_entry(displayname)
        self.listbox.connect('row-activated', self.on_profile_chosen)
        layout.pack_start(self.listbox, expand=True, fill=True, padding=0)
        layout.set_margin_start(100)
        layout.set_margin_end(100)
        layout.set_margin_top(50)
        layout.set_margin_bottom(50)
        add = Gtk.Button.new_with_label('Add')
        add.connect('clicked', self.on_add)
        layout.pack_start(add, expand=False, fill=False, padding=0)

        self.add(layout)
        self.connect('realize', self.on_realized)
        self.connect('destroy', self.on_closed)
        self.show_all()

    def add_listbox_entry(self, displayname):
        row = Gtk.ListBoxRow()
        row.add(Gtk.Label(label=displayname))
        self.listbox.add(row)

    def on_add(self, widget):
        add_dialog = Gtk.Dialog()
        vbox = add_dialog.get_content_area()
        grid = Gtk.Grid()
        grid.set_column_spacing(4)
        grid.set_row_spacing(4)
        grid.set_margin_start(8)
        grid.set_margin_end(8)
        grid.set_margin_top(8)
        grid.set_margin_bottom(8)
        vbox.add(grid)

        y = 0
        grid.attach(Gtk.Label(label="Display name"), left=0, top=y, width=1, height=1)
        displayname_entry = Gtk.Entry()
        grid.attach(displayname_entry, left=1, top=y, width=1, height=1)

        y = 1
        grid.attach(Gtk.Label(label="Config file"), left=0, top=y, width=1, height=1)
        filepath_entry = Gtk.Entry()
        grid.attach(filepath_entry, left=1, top=y, width=1, height=1)

        add_dialog.add_buttons("Select", 1,
                               "Cancel", 0)
        add_dialog.show_all()
        response = add_dialog.run()
        if response:
            self.mru.append((displayname_entry.get_text(), filepath_entry.get_text()))
            self.add_listbox_entry(displayname_entry.get_text())
            self.listbox.show_all()
        add_dialog.destroy()

    def on_closed(self, widget):
        self.completion_callback(None)

    def on_realized(self, widget):
        self.set_size_request(640, 480)
        self.set_position(Gtk.WindowPosition.CENTER)

    def on_profile_chosen(self, listbox, row):
        self.disconnect_by_func(self.on_closed)  # ensure we don't call the completion callback twice
        self.completion_callback(pathlib.Path(self.mru[row.get_index()][1]))
