import pathlib
from config import Config

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this


class EditConfigDialog(Gtk.Dialog):
    def __init__(self, parent, config: Config):
        super().__init__(title=f"Configuration {config.filename.name}", transient_for=parent, flags=0)

        self.stack = Gtk.Stack()

        general_grid = self._init_general_grid(config)
        self.stack.add_titled(general_grid, "general", "General")

        executables_grid = self._init_executables_grid(config)
        self.stack.add_titled(executables_grid, "executables", "Executables")

        switcher = Gtk.StackSwitcher()
        switcher.set_stack(self.stack)

        # TODO: Other things for the config:
        #    filetypes
        #    maybe non-default ftp

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.pack_start(switcher, expand=True, fill=True, padding=0)
        vbox.pack_start(self.stack, expand=True, fill=True, padding=0)
        self.get_content_area().add(vbox)

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.set_default_size(350, 100)

        self.show_all()

    def _init_general_grid(self, config: Config):
        grid = Gtk.Grid()
        grid.set_column_spacing(4)
        grid.set_row_spacing(4)
        grid.set_margin_start(8)
        grid.set_margin_end(8)
        grid.set_margin_top(8)
        grid.set_margin_bottom(8)
        grid.set_hexpand(True)
        grid.set_vexpand(False)

        y = 0
        grid.attach(Gtk.Label(label="Warm up music"), left=0, top=y, width=1, height=1)
        self.warm_up_entry = Gtk.Entry()
        self.warm_up_entry.set_text(str(config.warm_up_music_directory))
        self.warm_up_entry.set_hexpand(True)
        grid.attach(self.warm_up_entry, left=1, top=y, width=1, height=1)
        # TODO: Button to open a file dialog?

        y += 1
        grid.attach(Gtk.Label(label="Video cache"), left=0, top=y, width=1, height=1)
        self.video_cache_entry = Gtk.Entry()
        self.video_cache_entry.set_text(str(config.video_cache_directory))
        self.video_cache_entry.set_hexpand(True)
        grid.attach(self.video_cache_entry, left=1, top=y, width=1, height=1)
        # TODO: Button to open a file dialog?

        y += 1
        grid.attach(Gtk.Label(label="Default FTP"), left=0, top=y, width=1, height=1)
        adjustment = Gtk.Adjustment(value=config.ftp['default'], lower=0.0, upper=1000.0, step_increment=1.0,
                                    page_increment=5.0, page_size=0.0)
        self.ftp_spinner = Gtk.SpinButton.new(adjustment, 1.0, 0)
        grid.attach(self.ftp_spinner, left=1, top=y, width=1, height=1)

        return grid

    def _init_executables_grid(self, config: Config):
        grid = Gtk.Grid()
        grid.set_column_spacing(4)
        grid.set_row_spacing(4)
        grid.set_margin_start(8)
        grid.set_margin_end(8)
        grid.set_margin_top(8)
        grid.set_margin_bottom(8)
        grid.set_hexpand(True)
        grid.set_vexpand(False)

        self.executable_entries = {}
        for y, (binary, path) in enumerate(config.executables.items()):
            grid.attach(Gtk.Label(label=binary), left=0, top=y, width=1, height=1)
            entry = Gtk.Entry()
            entry.set_text(str(path) if path else '')
            entry.set_hexpand(True)
            grid.attach(entry, left=1, top=y, width=1, height=1)
            self.executable_entries[binary] = entry
            # TODO: Button to open a file dialog?

        return grid

    def validate_input(self):
        # General tab validation:
        for entry in (self.warm_up_entry, self.video_cache_entry):
            directory = pathlib.Path(entry.get_text())
            if not directory.is_dir():
                self.stack.set_visible_child_name("general")
                return f"{str(directory)} does not exist"
        # The spinner ensure input is numeric; nothing to validate
        # Executable tab validation:
        for entry in self.executable_entries.values():
            pathstr = entry.get_text()
            if pathstr.strip() == '':
                # An empty string is permitted
                continue
            path = pathlib.Path(pathstr)
            if not path.is_file():
                self.stack.set_visible_child_name("executables")
                return f"{str(path)} does not exist"
        return None

    def write_values_to_config(self, config: Config):
        # General tab
        config.warm_up_music_directory = pathlib.Path(self.warm_up_entry.get_text())
        config.video_cache_directory = pathlib.Path(self.video_cache_entry.get_text())
        config.ftp['default'] = int(self.ftp_spinner.get_value())

        # Executables tab
        for binary, entry in self.executable_entries.items():
            pathstr = entry.get_text()
            path = pathlib.Path(pathstr) if pathstr else None
            config.executables[binary] = path
