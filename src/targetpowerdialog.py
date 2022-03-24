import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk  # noqa: E402 # need to call require_version before we can call this


class TargetPowerDialog(Gtk.Dialog):
    def __init__(self, parent, video_name, default_ftp, video_ftp):
        super().__init__(title="Target Power", transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.set_default_size(150, 100)

        label = Gtk.Label(label=f"Video: {video_name}")

        content_box = self.get_content_area()
        content_box.add(label)

        # Radio button group:
        # 1st radio button: o Default (123)
        default_power_box = Gtk.Box(Gtk.Orientation.HORIZONTAL, 6)
        self.default_power_radio = Gtk.RadioButton.new_with_label(None, "Default")
        self.default_power_radio.connect("toggled", self.on_radio_button_toggled)
        default_power_box.add(self.default_power_radio)

        default_power_label = Gtk.Label(label=f"({default_ftp})")
        default_power_box.add(default_power_label)

        # 2nd radio button: o Specified [____]
        specified_power_box = Gtk.Box(Gtk.Orientation.HORIZONTAL, 6)
        self.specified_power_radio = Gtk.RadioButton.new_with_label_from_widget(self.default_power_radio, "Specified")
        self.specified_power_radio.connect("toggled", self.on_radio_button_toggled)
        specified_power_box.add(self.specified_power_radio)

        init_val = video_ftp if video_ftp else default_ftp
        adjustment = Gtk.Adjustment(value=init_val, lower=0.0, upper=1000.0, step_increment=1.0,
                                    page_increment=5.0, page_size=0.0)
        self.specified_power_value = Gtk.SpinButton.new(adjustment, 1.0, 0)
        specified_power_box.add(self.specified_power_value)

        # Add the radio buttons
        content_box.add(default_power_box)
        content_box.add(specified_power_box)

        # Set the initial state
        self.specified_power_radio.set_active(video_ftp is not None)
        self.on_radio_button_toggled(self.specified_power_radio)

        self.show_all()

    def on_radio_button_toggled(self, button):
        self.specified_power_value.set_sensitive(self.specified_power_radio.get_active())

    def get_target_power(self):
        """
        Returns the entered target power, or None if the default should be used
        """
        if self.specified_power_radio.get_active():
            return int(self.specified_power_value.get_value())
        else:
            return None
