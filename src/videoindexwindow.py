import logging
import sys

from config import Config
from sessionpreview import SessionPreview
from sessionwindow import SessionWindow
from stackwindowwithbuttoninterface import StackWindowWithButtonInterface
from targetpowerdialog import TargetPowerDialog
from videocache import VideoCache
from videofeed import VideoFeed

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GLib, Gtk, GdkPixbuf  # noqa: E402 # need to call require_version before we can call this


def load_icon(icons_to_try):
    theme = Gtk.IconTheme()

    for icon_to_try in icons_to_try:
        try:
            pixbuf = theme.load_icon(icon_to_try, 32, 0)
        except GLib.GError:
            continue
        return pixbuf

    logging.warning("Unable to find an icon to represent a downloaded video")

    return None


def downloaded_icon():
    return load_icon(['emblem-ok-symbolic',
                      'emblem-downloads',
                      'emblem-shared'])


def downloading_icon():
    return load_icon(['emblem-synchronizing-symbolic',
                      'emblem-synchronizing'])


def favourite_icon():
    return load_icon(['starred-symbolic',
                      'starred'])


def format_ftp(ftp):
    return str(ftp) if ftp else 'Dflt'


def format_max(maxval):
    return str(maxval) if maxval else 'Dflt'


class ListStoreColumns:
    Favourite = 0  # Pixbuf
    VideoName = 1  # str
    VideoType = 2  # str
    VideoDate = 3  # str
    EffectiveFTP = 4  # str
    EffectiveMax = 5  # str
    VideoDuration = 6  # str
    VideoDownloaded = 7  # Pixbuf
    VideoId = 8  # str
    ShowRow = 9  # bool


class VideoIndexWindow(StackWindowWithButtonInterface):
    # Initialisation methods: constructor, window creation, menu creation, ...
    def __init__(self,
                 main_window: Gtk.Window,
                 config: Config,
                 label: str,
                 session_feed: VideoFeed,
                 video_cache: VideoCache,
                 session_window: SessionWindow):
        super().__init__(config, label)
        self.main_window = main_window
        self.session_feed = session_feed
        self.video_cache = video_cache
        self.session_window = session_window
        self.stack = None
        self.list_store = None

        self.downloaded_icon = downloaded_icon()
        self.downloading_icon = downloading_icon()
        self.favourite_icon = favourite_icon()
        self.downloading_id = None  # the id of the video that we are showing is being downloaded

    def add_windows_to_stack(self, stack, window_name_to_handler):
        self.stack = stack

        self.list_store = self.build_list_store()
        self.show_favourites_or_all()
        self.list_store_favourite_filter = self.list_store.filter_new()
        self.list_store_favourite_filter.set_visible_column(ListStoreColumns.ShowRow)
        tree = Gtk.TreeView(self.list_store_favourite_filter)
        self.tree = tree
        tree.connect('cursor-changed', self.on_index_selection_changed)
        tree.connect('row-activated', self.on_video_button_clicked)
        tree.connect('size-allocate', self.set_column_widths)
        tree.connect('button-press-event', self.on_button_press)
        tree.set_enable_search(False)

        favourite_renderer = Gtk.CellRendererPixbuf()
        self.fav_column = Gtk.TreeViewColumn("Favourite", favourite_renderer, pixbuf=ListStoreColumns.Favourite)
        tree.append_column(self.fav_column)

        title_renderer = Gtk.CellRendererText()
        self.title_column = Gtk.TreeViewColumn("Title", title_renderer, text=ListStoreColumns.VideoName)
        self.title_column.set_sort_column_id(ListStoreColumns.VideoName)
        tree.append_column(self.title_column)

        type_renderer = Gtk.CellRendererText()
        self.type_column = Gtk.TreeViewColumn("Type", type_renderer, text=ListStoreColumns.VideoType)
        self.type_column.set_sort_column_id(ListStoreColumns.VideoType)
        tree.append_column(self.type_column)

        duration_renderer = Gtk.CellRendererText()
        self.duration_column = Gtk.TreeViewColumn("Duration", duration_renderer, text=ListStoreColumns.VideoDuration)
        self.duration_column.set_sort_column_id(ListStoreColumns.VideoDuration)
        tree.append_column(self.duration_column)

        date_renderer = Gtk.CellRendererText()
        self.date_column = Gtk.TreeViewColumn("Date", date_renderer, text=ListStoreColumns.VideoDate)
        self.date_column.set_sort_column_id(ListStoreColumns.VideoDate)
        tree.append_column(self.date_column)

        ftp_renderer = Gtk.CellRendererText()
        self.ftp_column = Gtk.TreeViewColumn("FTP", ftp_renderer, text=ListStoreColumns.EffectiveFTP)
        self.ftp_column.set_sort_column_id(ListStoreColumns.EffectiveFTP)
        tree.append_column(self.ftp_column)

        max_renderer = Gtk.CellRendererText()
        self.max_column = Gtk.TreeViewColumn("Max", max_renderer, text=ListStoreColumns.EffectiveMax)
        self.max_column.set_sort_column_id(ListStoreColumns.EffectiveMax)
        tree.append_column(self.max_column)

        icon_renderer = Gtk.CellRendererPixbuf()
        self.icon_column = Gtk.TreeViewColumn("Downloaded", icon_renderer, pixbuf=ListStoreColumns.VideoDownloaded)
        tree.append_column(self.icon_column)

        scrollable_tree = Gtk.ScrolledWindow()
        scrollable_tree.set_vexpand(True)
        scrollable_tree.add(tree)

        self.session_preview = SessionPreview(self.config, self.session_feed.url)
        self.session_preview.set_vexpand(True)

        back_button = Gtk.Button(label='Back')
        back_button.connect('clicked', self.on_back_button_clicked)
        back_button.set_vexpand(False)

        grid = Gtk.Grid()
        grid.set_margin_top(100)
        grid.set_margin_bottom(100)
        grid.set_margin_left(200)
        grid.set_margin_right(200)
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(False)
        grid.set_row_spacing(10)
        grid.attach(scrollable_tree, 0, 0, 1, 3)
        grid.attach(self.session_preview, 0, 3, 1, 2)
        grid.attach(back_button, 0, 5, 1, 1)

        index_window_name = "main_session_index_window"
        stack.add_named(grid, index_window_name)
        window_name_to_handler[index_window_name] = self

        grid.connect('realize', self.on_shown)
        tree.connect('key-press-event', self.on_key_press)

    def build_list_store(self):
        # columns in the tree model are indexed according to ListStoreColumn values
        list_store = Gtk.ListStore(GdkPixbuf.Pixbuf,  # fav
                                   str,  # name
                                   str,  # type
                                   str,  # date
                                   str,  # ftp
                                   str,  # max
                                   str,  # duration
                                   GdkPixbuf.Pixbuf,  # downloaded
                                   str,  # video id
                                   bool)  # show row
        for video in self.session_feed:
            fav = self.favourite_icon if (video.id in self.config.favourites) else None
            effective_ftp = format_ftp(self.config.get_power(video.id, 'FTP', expand_default=False))
            effective_max = format_max(self.config.get_power(video.id, 'MAX', expand_default=False))
            list_store.append([fav, video.name, video.type, video.date, effective_ftp, effective_max, video.duration,
                               None, video.id, True])
        return list_store

    def create_right_click_menu(self, row):
        row_video_id = self.list_store_favourite_filter[row][ListStoreColumns.VideoId]
        menu = Gtk.Menu()
        # Menu item 1: Toggle favourite
        fav_menu_item = Gtk.MenuItem(label="Un-favourite" if row_video_id in self.config.favourites else "Favourite")
        fav_menu_item.connect('activate', self.on_favourite_menu_item_clicked)
        menu.append(fav_menu_item)
        # Menu item 2: Edit target power
        power_menu_item = Gtk.MenuItem(label="Customise power targets...")
        power_menu_item.connect('activate', self.on_target_power_menu_item_clicked)
        menu.append(power_menu_item)
        # Tidy up
        menu.show_all()
        return menu

    # Event handlers

    def on_button_press(self, widget, event):
        if event.type != Gdk.EventType.BUTTON_PRESS or event.button != 3:
            # not a right-click
            return
        pos = self.tree.get_path_at_pos(event.x, event.y)
        if not pos:
            # not on a row
            return
        path, column, x, y = pos
        row = path.get_indices()[0]
        self.menu_item_row = row
        self.create_right_click_menu(row).popup_at_pointer(event)

    def on_index_selection_changed(self, widget):
        selected_row, _ = widget.get_cursor()
        video_id = self.list_store_favourite_filter[selected_row][ListStoreColumns.VideoId]
        self.session_preview.show(video_id)

    def on_key_press(self, widget, event):
        """
        Handle the following key-press events:
        'c': toggle whether all videos are shown or just favourites
        '*': toggle whether the currently selected row (ie. video) is a favourite
        Ctrl-P: show the target power dialog for the currently selected row (i.e. video)
        (or Command-P on a Mac)
        """
        logging.debug("videoindexwindow: key state=%s, keyval=%s", event.state, event.keyval)
        # keyval, mods
        # TODO: C&P from applicationwindow.py
        event_mods = event.state
        if sys.platform == 'darwin':
            # Command-Q is shown as GDK_MOD2_MASK | GDK_META_MASK
            # yet accelerator_parse('<Primary>Q') returns
            # just GDK_META_MASK. As we don't currently use
            # GDK_MOD2_MASK for anything else, this is a quick
            # hack.
            # But (flags &~ Gdk.ModifierType.MOD2_MASK) returns
            # an int, rather than a Gdk.ModifierType - hence
            # this convoluted expression.
            event_mods = (event_mods | Gdk.ModifierType.MOD2_MASK) ^ Gdk.ModifierType.MOD2_MASK

        if (event.keyval, event_mods) == Gtk.accelerator_parse('c'):
            # toggle between all and favourites
            self.toggle_all_or_favourites()
            return True
        elif (event.keyval, event_mods) in (Gtk.accelerator_parse('<Shift>asterisk'),
                                            Gtk.accelerator_parse('KP_Multiply')):
            row = self.get_selected_row()
            if row:
                self.toggle_favourite(row)
            return True
        elif (event.keyval, event_mods) == Gtk.accelerator_parse('<Primary>p') or \
             (event.keyval, event_mods) == Gtk.accelerator_parse('Right'):
            row = self.get_selected_row()
            if row:
                self.show_power_customisation_dialog(row)
        return False

    def get_selected_row(self):
        """
        A simplified wrapper around the Gtk get_selected_rows(), taking advantage of the
        fact that we have no nesting, and don't allow multiple selection.
        """
        _, treepaths = self.tree.get_selection().get_selected_rows()  # model is self.list_store_favourite_filter
        for treepath in treepaths:
            return treepath.get_indices()[0]
        return None

    def on_main_button_clicked(self, widget):
        self.update_download_icons()
        if self.downloading_id:
            GLib.timeout_add_seconds(2, self.on_check_download_complete)
        # and show the index of videos
        assert self.stack
        self.stack.set_visible_child_name("main_session_index_window")

    def on_back_button_clicked(self, widget):
        self.stack.set_visible_child_name("main_window_buttons")

    def on_check_download_complete(self):
        if self.downloading_id is None:
            return False  # don't call me again
        if self.video_cache.active_download_id != self.downloading_id:
            self.update_download_icons()
        return self.downloading_id is not None

    def on_shown(self, widget):
        self.tree.grab_focus()
        self.tree.set_cursor(0, None, False)

    def on_video_button_clicked(self, widget, selected_row, column):
        # widget is the Button (in the ListBoxRow)
        logging.debug("Playing video %s (%s)",
                      self.list_store_favourite_filter[selected_row][ListStoreColumns.VideoName],
                      self.list_store_favourite_filter[selected_row][ListStoreColumns.VideoId])
        video_id = self.list_store_favourite_filter[selected_row][ListStoreColumns.VideoId]
        video_file = self.video_cache.cached_downloads.get(video_id)
        if video_file:
            self.session_window.play(video_file, video_id)
            self.stack.set_visible_child_name("session_window")
        # TODO: Report that video file not known

    def on_favourite_menu_item_clicked(self, menu_item):
        self.toggle_favourite(self.menu_item_row)

    def on_target_power_menu_item_clicked(self, menu_item):
        self.show_power_customisation_dialog(self.menu_item_row)

    # Action methods, typically called from the event handlers

    def show_power_customisation_dialog(self, row):
        video_id = self.list_store_favourite_filter[row][ListStoreColumns.VideoId]
        video_name = self.list_store_favourite_filter[row][ListStoreColumns.VideoName]
        default_ftp = self.config.get_power('default', 'FTP', expand_default=False)
        video_ftp = self.config.get_power(video_id, 'FTP', expand_default=False)
        default_max = self.config.get_power('default', 'MAX', expand_default=False)
        video_max = self.config.get_power(video_id, 'MAX', expand_default=False)
        dialog = TargetPowerDialog(parent=self.main_window, video_name=video_name,
                                   default_ftp=default_ftp, video_ftp=video_ftp,
                                   default_max=default_max, video_max=video_max)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            new_video_ftp = dialog.get_target_ftp()
            new_video_max = dialog.get_target_max()
            logging.debug(f"Target power dialog result: FTP: {new_video_ftp} Max: {new_video_max}")
            self.config.set_power(video_id, 'FTP', new_video_ftp)
            self.config.set_power(video_id, 'MAX', new_video_max)
            self.list_store_favourite_filter[row][ListStoreColumns.EffectiveFTP] = format_ftp(new_video_ftp)
            self.list_store_favourite_filter[row][ListStoreColumns.EffectiveMax] = format_max(new_video_max)
            self.config.save()
        dialog.destroy()

    def toggle_all_or_favourites(self):
        logging.debug("videoindexwindow: toggle_all_or_favourites")
        self.config.show_favourites_only = not self.config.show_favourites_only
        self.show_favourites_or_all()
        self.on_index_selection_changed(self.tree)
        self.config.save()

    def show_favourites_or_all(self):
        for row in self.list_store:
            if self.config.show_favourites_only:
                show = (row[ListStoreColumns.Favourite] is not None)
            else:
                show = True
            row[ListStoreColumns.ShowRow] = show

    def toggle_favourite(self, row):
        video_id = self.list_store_favourite_filter[row][ListStoreColumns.VideoId]
        if video_id in self.config.favourites:
            # remove it
            self.config.favourites.remove(video_id)
            self.list_store_favourite_filter[row][ListStoreColumns.Favourite] = None
            logging.debug("Favourite removed: %s [%s]", row, video_id)
        else:
            # add it
            self.config.favourites.append(video_id)
            self.list_store_favourite_filter[row][ListStoreColumns.Favourite] = self.favourite_icon
            logging.debug("Favourite added: %s [%s]", row, video_id)
        self.config.save()

    def set_column_widths(self, widget, allocation):
        new_icon_width = 100
        extra_space = self.icon_column.get_width() - new_icon_width

        for column, sizing in [(self.title_column, Gtk.TreeViewColumnSizing.AUTOSIZE),
                               (self.type_column, Gtk.TreeViewColumnSizing.GROW_ONLY),
                               (self.date_column, Gtk.TreeViewColumnSizing.GROW_ONLY),
                               (self.duration_column, Gtk.TreeViewColumnSizing.GROW_ONLY)]:
            column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
            column.set_resizable(True)
            if extra_space > 0:
                column.set_min_width(column.get_width() + extra_space / 4)

        self.icon_column.set_fixed_width(new_icon_width)
        self.icon_column.set_max_width(new_icon_width)
        self.icon_column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.icon_column.set_resizable(False)

    def update_download_icons(self):
        # Update the display whether files are in the cache
        self.downloading_id = None
        for row in self.list_store:
            video_id = row[ListStoreColumns.VideoId]
            if self.video_cache.cached_downloads.get(video_id):
                row[ListStoreColumns.VideoDownloaded] = self.downloaded_icon
            elif self.video_cache.active_download_id == video_id:
                self.downloading_id = video_id
                row[ListStoreColumns.VideoDownloaded] = self.downloading_icon
            else:
                row[ListStoreColumns.VideoDownloaded] = None

    # StackWindowWithButtonInterface compatibility

    def handle_volume_change(self, change):
        pass

    def is_playing(self):
        return False

    def play_pause(self):
        pass

    def stop(self):
        pass
