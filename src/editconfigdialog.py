import logging
import os
import pathlib

from config import Config
from players import PlayerLookup

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk  # noqa: E402 # need to call require_version before we can call this


margin_labels_and_names = [
    ('Top margin', 'margin_top'),
    ('Bottom margin', 'margin_bottom'),
    ('Left margin', 'margin_left'),
    ('Right margin', 'margin_right')
]


def create_grid():
    grid = Gtk.Grid()
    grid.set_column_spacing(4)
    grid.set_row_spacing(4)
    grid.set_margin_start(8)
    grid.set_margin_end(8)
    grid.set_margin_top(8)
    grid.set_margin_bottom(8)
    grid.set_hexpand(True)
    grid.set_vexpand(False)
    return grid


def create_integer_spinner(lower, upper, value):
    adjustment = Gtk.Adjustment(value=value, lower=lower, upper=upper, step_increment=1.0,
                                page_increment=5.0, page_size=0.0)
    return Gtk.SpinButton.new(adjustment, 1.0, 0)


class EditConfigDialog(Gtk.Dialog):
    def __init__(self, parent, config: Config):
        super().__init__(title=f"Configuration {config.filename.name}", transient_for=parent, flags=0)
        self.parent = parent

        self.stack = Gtk.Stack()

        self.to_hide = []

        general_grid = self._init_general_grid(config)
        self.stack.add_titled(general_grid, "general", "General")

        executables_grid = self._init_executables_grid(config)
        self.stack.add_titled(executables_grid, "executables", "Executables")

        filetypes_grid = self._init_filetypes_grid(config)
        self.stack.add_titled(filetypes_grid, "filetypes", "Filetypes")

        switcher = Gtk.StackSwitcher()
        switcher.set_stack(self.stack)

        # TODO: Maybe add view/edit of the non-default FTPs

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.pack_start(switcher, expand=True, fill=True, padding=0)
        vbox.pack_start(self.stack, expand=True, fill=True, padding=0)
        self.get_content_area().add(vbox)

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        # self.set_default_size(350, 100)

        self.ftp_spinner.connect('key-press-event', self.on_key_press)

        self.show_all()
        # selectively undo the effects of show_all
        for to_hide in self.to_hide:
            to_hide.hide()

        self.set_default_response(Gtk.ResponseType.OK)

    def _init_general_grid(self, config: Config):
        grid = create_grid()

        self.label_for_entry = {}

        y = 0
        warm_up_label = "Warm up music"
        grid.attach(Gtk.Label(label=warm_up_label), left=0, top=y, width=1, height=1)
        self.warm_up_entry = Gtk.Entry()
        self.warm_up_entry.set_text(str(config.warm_up_music_directory))
        self.warm_up_entry.set_hexpand(True)
        self.warm_up_entry.connect('changed', self.on_directory_entry_changed)
        self.label_for_entry[self.warm_up_entry] = warm_up_label
        grid.attach(self.warm_up_entry, left=1, top=y, width=1, height=1)
        # TODO: Button to open a file dialog?

        y += 1
        video_cache_label = "Video cache"
        grid.attach(Gtk.Label(label=video_cache_label), left=0, top=y, width=1, height=1)
        self.video_cache_entry = Gtk.Entry()
        self.video_cache_entry.set_text(str(config.video_cache_directory))
        self.video_cache_entry.set_hexpand(True)
        self.video_cache_entry.connect('changed', self.on_directory_entry_changed)
        self.label_for_entry[self.video_cache_entry] = video_cache_label
        grid.attach(self.video_cache_entry, left=1, top=y, width=1, height=1)
        # TODO: Button to open a file dialog?

        y += 1
        grid.attach(Gtk.Label(label="Default FTP"), left=0, top=y, width=1, height=1)
        self.ftp_spinner = create_integer_spinner(0, 1000, config.ftp['default'])
        self.ftp_spinner.set_activates_default(True)  # TODO: Move into create_integer_spinner?
        grid.attach(self.ftp_spinner, left=1, top=y, width=1, height=1)

        return grid

    def _init_executables_grid(self, config: Config):
        grid = create_grid()
        self.executable_entries = {}
        for y, (binary, path) in enumerate(config.executables.items()):
            grid.attach(Gtk.Label(label=binary), left=0, top=y, width=1, height=1)
            entry = Gtk.Entry()
            entry.set_text(str(path) if path else '')
            entry.set_hexpand(True)
            entry.connect('changed', self.on_executable_changed)
            grid.attach(entry, left=1, top=y, width=1, height=1)
            self.executable_entries[binary] = entry
            # TODO: Button to open a file dialog?

        return grid

    def _init_filetypes_grid(self, config: Config):
        grid = create_grid()
        self.filetype_comboboxes = {}
        self.filetype_from_combobox = {}
        self.filetype_args_entries = {}
        self.filetype_params_buttons = {}
        self.filetype_from_params_button = {}
        self.omxplayer_params = {}
        valid_players_list = list(PlayerLookup.keys())
        logging.debug(valid_players_list)
        for y, (filetype, player) in enumerate(config.players.items()):
            logging.debug(f"filetype: {filetype}: player={player.name if player else None}")
            # x0: label
            grid.attach(Gtk.Label(label=filetype), left=0, top=y, width=1, height=1)
            # x1: combobox
            combobox = Gtk.ComboBoxText()
            combobox.set_entry_text_column(0)
            for valid_player in valid_players_list:
                combobox.append_text(valid_player)
            if player:
                combobox.set_active(valid_players_list.index(player.name))
            combobox.set_hexpand(False)
            combobox.connect('changed', self.on_filetype_player_combobox_changed)
            grid.attach(combobox, left=1, top=y, width=1, height=1)
            self.filetype_comboboxes[filetype] = combobox
            self.filetype_from_combobox[combobox] = filetype
            # x2: options and parameters
            # (parameters only relevant to omxplayer)
            opts_params_box = Gtk.Box(Gtk.Orientation.HORIZONTAL, 6)
            entry = Gtk.Entry()
            self.filetype_args_entries[filetype] = entry
            entry.set_text(' '.join(player.default_args))
            entry.set_hexpand(True)
            opts_params_box.add(entry)

            button = Gtk.Button(label="Parameters")
            button.connect('clicked', self.on_filetype_player_params_button_clicked)
            opts_params_box.add(button)
            grid.attach(opts_params_box, left=2, top=y, width=1, height=1)
            self.filetype_params_buttons[filetype] = button
            self.filetype_from_params_button[button] = filetype
            if player.name == 'omxplayer':
                self.omxplayer_params[filetype] = dict(player.player_parameters)
            else:
                self.omxplayer_params[filetype] = {}
                self.to_hide.append(button)

        return grid

    def on_directory_entry_changed(self, entry):
        validation_error = self.validate_directory_value(entry)
        self.show_entry_validation_status(entry, validation_error)

    def on_executable_changed(self, entry):
        validation_error = self.validate_executable_entry_value(entry)
        self.show_entry_validation_status(entry, validation_error)

    def show_entry_validation_status(self, entry, validation_error):
        ok = not bool(validation_error)
        fg = None if ok else Gdk.Color(50000, 0, 0)
        entry.modify_fg(Gtk.StateFlags.NORMAL, fg)

    def on_filetype_player_combobox_changed(self, combobox):
        filetype = self.filetype_from_combobox[combobox]
        new_player = combobox.get_active_text()
        show_params_button = (new_player == 'omxplayer')
        self.filetype_params_buttons[filetype].set_visible(show_params_button)

    def on_filetype_player_params_button_clicked(self, button):
        filetype = self.filetype_from_params_button[button]
        params_dialog = OmxplayerParamsDialog(self.parent, filetype, self.omxplayer_params[filetype])
        if params_dialog.run() == Gtk.ResponseType.OK:
            for _, margin_name in margin_labels_and_names:
                self.omxplayer_params[filetype][margin_name] = params_dialog.get_margin(margin_name)
        params_dialog.destroy()

    def on_key_press(self, widget, event):
        stop_propagation = True
        allow_propagation = False
        if (event.keyval, event.state) == Gtk.accelerator_parse('Up'):
            logging.debug("Up: setting focus to video cache entry box")
            self.set_focus(self.video_cache_entry)
            return stop_propagation
        elif (event.keyval, event.state) == Gtk.accelerator_parse('Down'):
            logging.debug("Down: setting focus to OK button")
            ok_button = self.get_widget_for_response(Gtk.ResponseType.OK)
            self.set_focus(ok_button)
            return stop_propagation
        elif (event.keyval, event.state) == Gtk.accelerator_parse('Left'):
            logging.debug("Left: Decrement value")
            self.ftp_spinner.spin(Gtk.SpinType.STEP_BACKWARD, 1)
            return stop_propagation
        elif (event.keyval, event.state) == Gtk.accelerator_parse('Right'):
            logging.debug("Right: Increment value")
            self.ftp_spinner.spin(Gtk.SpinType.STEP_FORWARD, 1)
            return stop_propagation
        logging.debug("Another key event: %s + %s", event.state, event.keyval)
        return allow_propagation

    def validate_directory_value(self, entry):
        label = self.label_for_entry[entry]
        pathstr = entry.get_text()
        if pathstr.strip() == '':
            return f"{label} directory must be specified"
        directory = pathlib.Path(pathstr)
        if not directory.is_dir():
            return f"{str(directory)} does not exist"
        return None

    def validate_executable_entry_value(self, entry):
        pathstr = entry.get_text()
        if pathstr.strip() == '':
            # An empty string is permitted
            return None
        path = pathlib.Path(pathstr)
        if not path.is_file():
            return f"{str(path)} is not a file" if path.exists() else f"{str(path)} does not exist"
        if not os.access(path, os.X_OK):
            return f"{str(path)} is not executable"
        return None

    def validate_input(self):
        # General tab validation:
        for entry in [self.warm_up_entry, self.video_cache_entry]:
            msg = self.validate_directory_value(entry)
            if msg:
                self.stack.set_visible_child_name("general")
                return msg
        # The spinner ensure input is numeric; nothing to validate
        # Executable tab validation:
        for entry in self.executable_entries.values():
            msg = self.validate_executable_entry_value(entry)
            if msg:
                self.stack.set_visible_child_name("executables")
                return msg

        # Filetypes tab validation:
        # combobox enforces sensible options
        # no sensible validation of default args possible
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

        # Filetypes tab
        for filetype in config.players.keys():
            combobox = self.filetype_comboboxes[filetype]
            player_name = combobox.get_active_text()
            entry = self.filetype_args_entries[filetype]
            player_params = self.omxplayer_params[filetype] if player_name == 'omxplayer' else {}
            config.set_filetype_player(filetype,
                                       player_name,
                                       entry.get_text().split(' '),
                                       player_params)


class OmxplayerParamsDialog(Gtk.Dialog):
    def __init__(self, parent, filetype, init_params):
        super().__init__(title=f"omxplayer parameters for {filetype}", transient_for=parent, flags=0)

        self.spinners = {}

        grid = create_grid()
        for y, (label_str, margin_name) in enumerate(margin_labels_and_names):
            grid.attach(Gtk.Label(label=label_str), left=0, top=y, width=1, height=1)
            self.spinners[margin_name] = create_integer_spinner(-1024, 1024, init_params.get(margin_name, 0))
            grid.attach(self.spinners[margin_name], left=1, top=y, width=1, height=1)

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.get_content_area().add(grid)
        self.show_all()

    def get_margin(self, margin_name):
        return int(self.spinners[margin_name].get_value())
