import logging
import sys

from config import Config
from sessionpreview import SessionPreview
from sessionwindow import SessionWindow
from stackwindowwithbuttoninterface import StackWindowWithButtonInterface
from videocache import VideoCache
from videofeed import VideoFeed

import gi
gi.require_version('Gtk', '3.0')
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


class ListStoreColumns:
    Favourite = 0
    VideoName = 1
    VideoType = 2
    VideoDate = 3
    VideoDuration = 4
    VideoDownloaded = 5
    VideoId = 6
    ShowRow = 7


class VideoIndexWindow(StackWindowWithButtonInterface):
    def __init__(self,
                 config: Config,
                 label: str,
                 session_feed: VideoFeed,
                 video_cache: VideoCache,
                 session_window: SessionWindow):
        super().__init__(config, label)
        self.session_feed = session_feed
        self.video_cache = video_cache
        self.session_window = session_window
        self.stack = None
        self.list_store = None

        self.downloaded_icon = downloaded_icon()
        self.downloading_icon = downloading_icon()
        self.favourite_icon = favourite_icon()
        self.downloading_id = None  # the id of the video that we are showing is being downloaded

    def build_list_store(self):
        # columns in the tree model are indexed according to ListStoreColumn values
        list_store = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str, str, GdkPixbuf.Pixbuf, str, bool)
        for video in self.session_feed:
            fav = self.favourite_icon if (video.id in self.config.favourites) else None
            list_store.append([fav, video.name, video.type, video.date, video.duration, None, video.id, True])
        return list_store

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
        tree.set_enable_search(False)

        favourite_renderer = Gtk.CellRendererPixbuf()
        self.fav_column = Gtk.TreeViewColumn("Favourite", favourite_renderer, pixbuf=ListStoreColumns.Favourite)
        tree.append_column(self.fav_column)

        title_renderer = Gtk.CellRendererText()
        self.title_column = Gtk.TreeViewColumn("Title", title_renderer, text=ListStoreColumns.VideoName)
        self.title_column.set_sort_column_id(0)
        tree.append_column(self.title_column)

        type_renderer = Gtk.CellRendererText()
        self.type_column = Gtk.TreeViewColumn("Type", type_renderer, text=ListStoreColumns.VideoType)
        self.type_column.set_sort_column_id(1)
        tree.append_column(self.type_column)

        duration_renderer = Gtk.CellRendererText()
        self.duration_column = Gtk.TreeViewColumn("Duration", duration_renderer, text=ListStoreColumns.VideoDuration)
        self.duration_column.set_sort_column_id(3)
        tree.append_column(self.duration_column)

        date_renderer = Gtk.CellRendererText()
        self.date_column = Gtk.TreeViewColumn("Date", date_renderer, text=ListStoreColumns.VideoDate)
        self.date_column.set_sort_column_id(2)
        tree.append_column(self.date_column)

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

    def on_index_selection_changed(self, widget):
        selected_row, _ = widget.get_cursor()
        video_id = self.list_store_favourite_filter[selected_row][ListStoreColumns.VideoId]
        self.session_preview.show(video_id)

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

    def on_key_press(self, widget, event):
        logging.debug("videoindexwindow: key state=%s, keyval=%s", event.state, event.keyval)
        if (event.state, event.keyval) == (Gdk.ModifierType(0), ord('c')):
            # toggle between all and favourites
            self.toggle_all_or_favourites()
            return True
        elif (event.state, event.keyval) in ((Gdk.ModifierType.SHIFT_MASK, Gdk.KEY_asterisk),
                                             (Gdk.ModifierType(0), Gdk.KEY_KP_Multiply)):
            _, treepaths = self.tree.get_selection().get_selected_rows()  # model is self.list_store_favourite_filter
            for treepath in treepaths:
                row = treepath.get_indices()[0]
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
            return True
        return False

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

    def handle_volume_change(self, change):
        pass

    def is_playing(self):
        return False

    def play_pause(self):
        pass

    def stop(self):
        pass
