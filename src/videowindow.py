import logging
import sys

from config import Config
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


class MainSessionIndexWindow(PlayerWindowInterface):
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

        self.downloaded_icon = downloaded_icon()
        self.downloading_icon = downloading_icon()
        self.downloading_id = None  # the id of the video that we are showing is being downloaded

    def build_list_store(self):
        # columns in the tree model:
        #   0: video name (str)
        #   1: video id (str)
        #   2: video date (str)
        #   3: video duration (str)
        #   4: download status (pixbuf)
        list_store = Gtk.ListStore(str, str, str, str, GdkPixbuf.Pixbuf)
        for video in self.session_feed:
            list_store.append([video.name, video.id, video.date, video.duration, None])
        return list_store

    def add_windows_to_stack(self, stack):
        self.stack = stack

        self.list_store = self.build_list_store()
        tree = Gtk.TreeView(self.list_store)
        tree.connect('row-activated', self.on_video_button_clicked)

        title_renderer = Gtk.CellRendererText()
        title_column = Gtk.TreeViewColumn("Title", title_renderer, text=0)
        title_column.set_sort_column_id(0)
        tree.append_column(title_column)

        date_renderer = Gtk.CellRendererText()
        date_column = Gtk.TreeViewColumn("Date", date_renderer, text=2)
        date_column.set_sort_column_id(2)
        tree.append_column(date_column)

        duration_renderer = Gtk.CellRendererText()
        duration_column = Gtk.TreeViewColumn("Duration", duration_renderer, text=3)
        duration_column.set_sort_column_id(3)
        tree.append_column(duration_column)

        icon_renderer = Gtk.CellRendererPixbuf()
        icon_column = Gtk.TreeViewColumn("Status", icon_renderer, pixbuf=4)
        tree.append_column(icon_column)

        scrollable_tree = Gtk.ScrolledWindow()
        scrollable_tree.set_vexpand(True)
        scrollable_tree.add(tree)

        back_button = Gtk.Button(label='Back')
        back_button.connect('clicked', self.on_back_button_clicked)
        vbox = Gtk.VBox()
        vbox.pack_start(scrollable_tree, expand=True, fill=True, padding=10)
        vbox.pack_start(back_button, expand=False, fill=True, padding=10)
        stack.add_named(vbox, "main_session_index_window")

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

    def on_video_button_clicked(self, widget, selected_row, column):
        # widget is the Button (in the ListBoxRow)
        video_id = self.list_store[selected_row][1]
        video_file = self.video_cache.cached_downloads.get(video_id)
        if video_file:
            # play it!
            player = self.config.players[video_file.suffix]
            player.play(video_file)

    def update_download_icons(self):
        # Update the display whether files are in the cache
        self.downloading_id = None
        for row in self.list_store:
            video_id = row[1]
            if self.video_cache.cached_downloads.get(video_id):
                row[4] = self.downloaded_icon
            elif row.feed_item and self.video_cache.active_download_id == video_id:
                self.downloading_id = video_id
                row[4] = self.downloading_icon
            else:
                row[4] = None

    def stop(self):
        pass  # TODO
