from collections import namedtuple
import logging

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this

PageControls = namedtuple('PageControls', 'box, radio_buttons, radio_to_spinner, spinner_to_radio')


class TargetPowerDialog(Gtk.Dialog):
    def _build_default_power_box(self, default_power):
        default_power_box = Gtk.Box(Gtk.Orientation.HORIZONTAL, 6)
        default_power_radio = Gtk.RadioButton.new_with_label(None, "Default")
        default_power_radio.connect("toggled", self.on_radio_button_toggled)
        default_power_box.add(default_power_radio)
        default_power_label = Gtk.Label(label=f"({default_power})")
        default_power_box.add(default_power_label)
        return default_power_box, default_power_radio

    def _build_absolute_power_box(self, default_power_radio, init_val: int, is_active: bool):
        absolute_power_box = Gtk.Box(Gtk.Orientation.HORIZONTAL, 6)
        specified_power_radio = Gtk.RadioButton.new_with_label_from_widget(default_power_radio, "Power")
        specified_power_radio.connect("toggled", self.on_radio_button_toggled)
        absolute_power_box.add(specified_power_radio)

        adjustment = Gtk.Adjustment(value=init_val, lower=0.0, upper=1000.0, step_increment=1.0,
                                    page_increment=5.0, page_size=0.0)
        specified_power_spinbutton = Gtk.SpinButton.new(adjustment, 1.0, 0)
        specified_power_spinbutton.set_activates_default(True)
        absolute_power_box.add(specified_power_spinbutton)

        # Set the initial state for the radios
        specified_power_radio.set_active(is_active)
        specified_power_spinbutton.set_sensitive(is_active)
        return absolute_power_box, specified_power_radio, specified_power_spinbutton

    def _build_relative_power_box(self, default_power_radio, init_val: int, is_active: bool):
        relative_power_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
        relative_power_radio = Gtk.RadioButton.new_with_label_from_widget(default_power_radio, r"%FTP")
        relative_power_radio.connect("toggled", self.on_radio_button_toggled)
        relative_power_box.add(relative_power_radio)

        adjustment = Gtk.Adjustment(value=init_val, lower=0.0, upper=500.0, step_increment=1.0,
                                    page_increment=5.0, page_size=0.0)
        specified_power_spinbutton = Gtk.SpinButton.new(adjustment, 1.0, 0)
        specified_power_spinbutton.set_activates_default(True)
        relative_power_box.add(specified_power_spinbutton)

        # Set the initial state for the radios
        relative_power_radio.set_active(is_active)
        specified_power_spinbutton.set_sensitive(is_active)
        return relative_power_box, relative_power_radio, specified_power_spinbutton

    def _build_ftp_page(self, default_ftp, video_ftp):
        logging.debug(f"_build_page_content: default {default_ftp}, specified {video_ftp}")
        # Radio button group:
        # 1st radio button: o Default (123)
        default_ftp_box, default_ftp_radio = self._build_default_power_box(default_ftp)
        # 2nd radio button: o Power [____]
        init_absolute = video_ftp or default_ftp
        absolute_active = video_ftp is not None
        absolute_ftp_box, absolute_ftp_radio, absolute_ftp_spinbutton = self._build_absolute_power_box(default_ftp_radio, init_absolute, absolute_active)

        # Assemble the page of settings
        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box.add(default_ftp_box)
        box.add(absolute_ftp_box)
        return PageControls(box,
                            radio_buttons=[default_ftp_radio, absolute_ftp_radio],
                            radio_to_spinner={absolute_ftp_radio: absolute_ftp_spinbutton},
                            spinner_to_radio={absolute_ftp_spinbutton: absolute_ftp_radio})

    def _build_max_page(self, default_ftp, default_max, video_max):
        logging.debug(f"_build_max_page: default {default_max}, video {video_max}")
        # Radio button group:
        # 1st radio button: o Default (123)
        default_max_box, default_max_radio = self._build_default_power_box(default_max)
        # 2nd radio button: o Power [____]
        absolute_active = video_max and not video_max.endswith('%')
        if absolute_active:
            init_absolute = int(video_max)
        else:
            init_absolute = int(default_max) if default_max and not default_max.endswith('%') else default_ftp
        absolute_max_box, absolute_max_radio, absolute_max_spinbutton = self._build_absolute_power_box(default_max_radio, init_absolute, absolute_active)
        # 3rd radio button: o %FTP [____]
        relative_active = video_max and video_max.endswith('%')
        if relative_active:
            init_relative = int(video_max[:-1])
        else:
            init_relative = int(default_max[:-1]) if (default_max and default_max.endswith('%')) else 200
        relative_max_box, relative_max_radio, relative_max_spinbutton = self._build_relative_power_box(default_max_radio, init_relative, relative_active)

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        box.add(default_max_box)
        box.add(absolute_max_box)
        box.add(relative_max_box)
        return PageControls(box,
                            radio_buttons=[default_max_radio, absolute_max_radio, relative_max_radio],
                            radio_to_spinner={absolute_max_radio: absolute_max_spinbutton,
                                              relative_max_radio: relative_max_spinbutton},
                            spinner_to_radio={absolute_max_spinbutton: absolute_max_radio,
                                              relative_max_spinbutton: relative_max_radio})

    def __init__(self, parent, video_name, default_ftp, video_ftp, default_max, video_max):
        super().__init__(title="Power Customisations", transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.set_default_size(150, 100)

        label = Gtk.Label(label=f"Video: {video_name}")

        content_box = self.get_content_area()
        content_box.add(label)
        self.ftp_controls = self.max_controls = None  # building the page triggers some of the event handlers
        self.ftp_controls = self._build_ftp_page(default_ftp, video_ftp)
        self.max_controls = self._build_max_page(default_ftp, default_max, video_max)

        # Pages of settings
        self.notebook = Gtk.Notebook.new()
        self.notebook.append_page(self.ftp_controls.box, Gtk.Label("FTP"))
        self.notebook.append_page(self.max_controls.box, Gtk.Label("Max"))
        content_box.add(self.notebook)

        self.set_default_response(Gtk.ResponseType.OK)

        self.connect('key-press-event', self.on_key_press)

        self.show_all()

    def on_key_press(self, widget, event):
        stop_propagation = True
        allow_propagation = False
        is_down = (event.keyval, event.state) == Gtk.accelerator_parse('Down')
        is_up = (event.keyval, event.state) == Gtk.accelerator_parse('Up')
        is_left = (event.keyval, event.state) == Gtk.accelerator_parse('Left')
        is_right = (event.keyval, event.state) == Gtk.accelerator_parse('Right')
        is_enter = (event.keyval, event.state) == Gtk.accelerator_parse('Return')
        logging.debug(f"Keypress: down: {is_down}; up: {is_up}; left: {is_left}; right: {is_right}; enter: {is_enter}")
        focussed_ctrl = self.get_focus()
        logging.debug(f"  Control: {focussed_ctrl}")
        if (focussed_ctrl == self.notebook) and is_down:
            page = self.ftp_controls if (self.notebook.get_current_page() == 0) else self.max_controls
            self.set_focus(page.radio_buttons[0])
            return stop_propagation
        for page in (self.ftp_controls, self.max_controls):
            current_radio = None
            if focussed_ctrl in page.radio_buttons:
                current_radio = focussed_ctrl
                if is_enter:
                    if current_radio.get_active():
                        # A second 'return'/'OK' triggers the dialog OK
                        return allow_propagation
                    else:
                        # First 'return'/'OK' activates the radio button
                        focussed_ctrl.set_active(True)
                        spinner = page.radio_to_spinner.get(focussed_ctrl)
                        if spinner:
                            self.set_focus(spinner)
                        return stop_propagation
                # not enter - fall through to up/down handling
                pass
            elif focussed_ctrl in page.spinner_to_radio:
                if is_left:
                    focussed_ctrl.spin(Gtk.SpinType.STEP_BACKWARD, 1)
                    return stop_propagation
                elif is_right:
                    focussed_ctrl.spin(Gtk.SpinType.STEP_FORWARD, 1)
                    return stop_propagation
                current_radio = page.spinner_to_radio[focussed_ctrl]
                # fall-through to the radio button navigation
            if current_radio and (is_up or is_down):
                if is_up:
                    radio_delta = -1
                    to_focus_if_not_radio_button = self.notebook
                else:
                    radio_delta = 1
                    to_focus_if_not_radio_button = self.get_widget_for_response(Gtk.ResponseType.OK)
                current_index = page.radio_buttons.index(current_radio)
                next_index = current_index + radio_delta
                if 0 <= next_index < len(page.radio_buttons):
                    next_radio = page.radio_buttons[next_index]
                    to_focus = next_radio
                else:
                    to_focus = to_focus_if_not_radio_button
                self.set_focus(to_focus)
                return stop_propagation
        return allow_propagation

    def on_radio_button_toggled(self, button):
        for page in (self.ftp_controls, self.max_controls):
            if not page:
                # The dialog is still being built
                continue
            spinner = page.radio_to_spinner.get(button)
            if spinner:
                spinner.set_sensitive(button.get_active())

    def get_target_ftp(self) -> int:
        """
        Returns the entered target power, or None if the default should be used
        """
        specified_ftp_radio = self.ftp_controls.radio_buttons[1]
        if specified_ftp_radio.get_active():
            spinner = self.ftp_controls.radio_to_spinner[specified_ftp_radio]
            return int(spinner.get_value())
        else:
            return None

    def get_target_max(self) -> str:
        """
        Returns the entered target power as:
          None: default should be used
          'nnn': an absolute power
          'nnn%': a power as a proportion of FTP
        """
        for radio_index, radio_button in enumerate(self.max_controls.radio_buttons):
            if radio_button.get_active():
                if radio_index == 0:
                    return None
                value = str(int(self.max_controls.radio_to_spinner[radio_button].get_value()))
                if radio_index == 2:
                    value += '%'
                return value
        logging.error("Unknown radio selected for max power")
        return None
