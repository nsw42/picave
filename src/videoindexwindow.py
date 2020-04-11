import logging
import sys

from config import Config
from intervalwindow import IntervalWindow
from sessionpreview import SessionPreview
from videocache import VideoCache
from videofeed import VideoFeed
from windowinterface import PlayerWindowInterface

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GdkPixbuf  # noqa: E402 # need to call require_version before we can call this


def load_icon(icons_to_try):
    theme = Gtk.IconTheme()
    if sys.platform == 'darwin':
        # default search path with `brew install adwaita-icon-theme` didn't work
        theme.append_search_path('/usr/local/Cellar/adwaita-icon-theme/3.34.3/share/icons/')  # TODO: Remove this??

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


class VideoIndexWindow(PlayerWindowInterface):
    def __init__(self,
                 config: Config,
                 label: str,
                 session_feed: VideoFeed,
                 video_cache: VideoCache):
        super().__init__(config, label)
        self.session_feed = session_feed
        self.video_cache = video_cache
        self.stack = None
        self.list_store = None
        self.player = None  # set when video starts

        self.downloaded_icon = downloaded_icon()
        self.downloading_icon = downloading_icon()
        self.downloading_id = None  # the id of the video that we are showing is being downloaded

        self.interval_window = IntervalWindow(config, session_feed.url)

    def build_list_store(self):
        # columns in the tree model:
        #   0: video name (str)
        #   1: video type (str)
        #   2: video date (str)
        #   3: video duration (str)
        #   4: download status (pixbuf)
        #   5: video id (str)
        list_store = Gtk.ListStore(str, str, str, str, GdkPixbuf.Pixbuf, str)
        for video in self.session_feed:
            list_store.append([video.name, video.type, video.date, video.duration, None, video.id])
        return list_store

    def add_windows_to_stack(self, stack):
        self.stack = stack

        self.list_store = self.build_list_store()
        tree = Gtk.TreeView(self.list_store)
        tree.connect('cursor-changed', self.on_index_selection_changed)
        tree.connect('row-activated', self.on_video_button_clicked)
        tree.connect('size-allocate', self.set_column_widths)

        title_renderer = Gtk.CellRendererText()
        self.title_column = Gtk.TreeViewColumn("Title", title_renderer, text=0)
        self.title_column.set_sort_column_id(0)
        tree.append_column(self.title_column)

        type_renderer = Gtk.CellRendererText()
        self.type_column = Gtk.TreeViewColumn("Type", type_renderer, text=1)
        self.type_column.set_sort_column_id(1)
        tree.append_column(self.type_column)

        duration_renderer = Gtk.CellRendererText()
        self.duration_column = Gtk.TreeViewColumn("Duration", duration_renderer, text=3)
        self.duration_column.set_sort_column_id(3)
        tree.append_column(self.duration_column)

        date_renderer = Gtk.CellRendererText()
        self.date_column = Gtk.TreeViewColumn("Date", date_renderer, text=2)
        self.date_column.set_sort_column_id(2)
        tree.append_column(self.date_column)

        icon_renderer = Gtk.CellRendererPixbuf()
        self.icon_column = Gtk.TreeViewColumn("Downloaded", icon_renderer, pixbuf=4)
        tree.append_column(self.icon_column)

        scrollable_tree = Gtk.ScrolledWindow()
        scrollable_tree.set_vexpand(True)
        scrollable_tree.add(tree)

        self.session_preview = SessionPreview(self.config, self.session_feed.url)

        back_button = Gtk.Button(label='Back')
        back_button.connect('clicked', self.on_back_button_clicked)
        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        grid.set_row_spacing(10)
        grid.attach(scrollable_tree, 0, 0, 1, 3)
        grid.attach(self.session_preview, 0, 3, 1, 2)

        vbox = Gtk.VBox()
        vbox.set_margin_top(100)
        vbox.set_margin_bottom(100)
        vbox.set_margin_left(200)
        vbox.set_margin_right(200)
        vbox.pack_start(grid, expand=True, fill=True, padding=10)
        vbox.pack_start(back_button, expand=False, fill=True, padding=10)
        stack.add_named(vbox, "main_session_index_window")

        video_layout = Gtk.HBox()
        video_layout.pack_start(self.interval_window, expand=True, fill=True, padding=0)  # TODO: Proper padding
        self.interval_window.set_margin_start(1500)  # pad on left side only
        stack.add_named(video_layout, "interval_window")

    def monitor_for_end_of_video(self):
        if self.player is None:
            still_playing = False
        elif self.player.is_finished():
            still_playing = False
        else:
            still_playing = True
        if not still_playing:
            self.player = None
            assert self.stack
            self.stack.set_visible_child_name("main_session_index_window")
        return still_playing

    def on_index_selection_changed(self, widget):
        selected_row, _ = widget.get_cursor()
        video_id = self.list_store[selected_row][5]
        self.session_preview.show(video_id)

    def on_main_button_clicked(self, widget):
        self.update_download_icons()
        if self.downloading_id:
            GLib.timeout_add_seconds(2, self.on_check_download_complete)
        # and show the index of videos
        assert self.stack
        self.stack.set_visible_child_name("main_session_index_window")

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

    def on_back_button_clicked(self, widget):
        self.stack.set_visible_child_name("main_window_buttons")

    def on_check_download_complete(self):
        if self.downloading_id is None:
            return False  # don't call me again
        if self.video_cache.active_download_id != self.downloading_id:
            self.update_download_icons()
        return self.downloading_id is not None

    def on_video_button_clicked(self, widget, selected_row, column):
        # widget is the Button (in the ListBoxRow)
        video_id = self.list_store[selected_row][5]
        video_file = self.video_cache.cached_downloads.get(video_id)
        if video_file:
            # play it!
            self.player = self.config.players[video_file.suffix]
            self.player.play(video_file)
        self.interval_window.play(video_id)
        self.stack.set_visible_child_name("interval_window")
        GLib.timeout_add_seconds(1, self.monitor_for_end_of_video)

    def update_download_icons(self):
        # Update the display whether files are in the cache
        self.downloading_id = None
        for row in self.list_store:
            video_id = row[5]
            if self.video_cache.cached_downloads.get(video_id):
                row[4] = self.downloaded_icon
            elif row.feed_item and self.video_cache.active_download_id == video_id:
                self.downloading_id = video_id
                row[4] = self.downloading_icon
            else:
                row[4] = None

    def stop(self):
        pass  # TODO
