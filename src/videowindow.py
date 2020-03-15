import logging
import sys

from config import Config
from videocache import VideoCache
from videofeed import VideoFeed, VideoFeedItem
from windowinterface import PlayerWindowInterface

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk  # noqa: E402 # need to call require_version before we can call this


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

        self.downloaded_icon = downloaded_icon()
        self.downloading_icon = downloading_icon()
        self.downloading_id = None  # the id of the video that we are showing is being downloaded

    def add_windows_to_stack(self, stack):
        self.stack = stack

        def row_button(label, handler, feed_item: VideoFeedItem):
            button = Gtk.Button(label=label)
            button.connect('clicked', handler)
            button.feed_item = feed_item
            button.set_can_focus(False)
            overlay = Gtk.Overlay()
            overlay.add(button)
            image = Gtk.Image()
            overlay.add_overlay(image)
            overlay.set_overlay_pass_through(image, True)
            # This next method is deprecated, but it actually works
            # The documentation shows a mismatch: Gtk.Image has
            # xalign / yalign, yet the Overlay looks at the
            # halign / valign parameters
            image.set_alignment(Gtk.Align.END, Gtk.Align.START)
            # the actual image is set when we show the window,
            # so that it reacts as the cache populates
            row = Gtk.ListBoxRow()
            row.feed_item = feed_item
            row.image = image
            row.add(overlay)
            row.connect('activate', handler)
            return row

        self.main_session_index_window = Gtk.ScrolledWindow()
        self.main_session_index_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
        self.main_session_listbox = Gtk.ListBox()
        self.main_session_index_window.add(self.main_session_listbox)
        for video in self.session_feed:
            self.main_session_listbox.add(row_button(video.name, self.on_video_button_clicked, video))
        self.main_session_listbox.add(row_button("Back", self.on_back_button_clicked, None))

        stack.add_named(self.main_session_index_window, "main_session_index_window")

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

    def on_video_button_clicked(self, widget):
        # widget is the Button (in the ListBoxRow)
        feed_item = widget.feed_item
        if feed_item:
            video_file = self.video_cache.cached_downloads.get(feed_item.id)
            if video_file:
                # play it!
                player = self.config.players[video_file.suffix]
                player.play(video_file)

    def update_download_icons(self):
        # Update the display whether files are in the cache
        index = 0
        self.downloading_id = None
        while True:
            row = self.main_session_listbox.get_row_at_index(index)
            if row is None:
                break
            if row.feed_item and self.video_cache.cached_downloads.get(row.feed_item.id):
                row.image.set_from_pixbuf(self.downloaded_icon)
            elif row.feed_item and self.video_cache.active_download_id == row.feed_item.id:
                self.downloading_id = row.feed_item.id
                row.image.set_from_pixbuf(self.downloading_icon)
            else:
                row.image.clear()
            index += 1

    def stop(self):
        pass  # TODO
