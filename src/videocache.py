import logging
import os
import subprocess
import threading

from config import Config
from videofeed import VideoFeed, VideoFeedItem


class VideoCache(object):
    def __init__(self,
                 config: Config,
                 feed: VideoFeed,
                 update_cache: bool):
        super().__init__()
        self.config = config
        self.feed = feed
        self.cached_downloads = {}
        self.update_cache = update_cache
        self.child_process = None  # subprocess.Popen instance
        self.terminate_download_thread_flag = None  # threading.Event
        self.active_download_id = None

        for feed_item in feed.items:
            self._init_download_cache(feed_item)  # populate self.cached_downloads

        self.youtube_dl = self.config.executables.get('youtube-dl')
        if update_cache and not all(self.cached_downloads.values()):
            if self.youtube_dl:
                self.start_filling_cache()
            else:
                logging.warn("youtube-dl not found. Unable to auto-populate video cache")

    def _find_youtube_cache(self,
                            feed_id: str):
        files = list(self.config.video_cache_directory.glob(feed_id + '.*'))
        if not files:
            return None
        if len(files) == 1:
            if files[0].suffix in ('.mp4', '.mkv'):
                return files[0]
            if files[0].suffix != '.part':
                logging.warning("Unfamiliar file extension on downloaded video file: %s" % files[0])
        # This may be a partial download, or maybe youtube-dl was interrupted
        # while merging the video and audio.  Either way, we'll need to continue.
        # Record that the video is not in the cache; youtube-dl will do the rest
        return None

    def _init_download_cache(self,
                             feed_item: VideoFeedItem):
        source, _ = feed_item.id.split('_')
        if source == 'yt':
            cache_file = self._find_youtube_cache(feed_item.id)
        else:
            raise Exception('Unrecognised feed video source')
        self.cached_downloads[feed_item.id] = cache_file

    def start_filling_cache(self):
        videos_to_download = []
        for feed_item in self.feed.items:
            if self.cached_downloads.get(feed_item.id) is None:
                videos_to_download.append(feed_item)
        if videos_to_download:
            self.download_thread = threading.Thread(target=self.download_videos,
                                                    args=[videos_to_download])
            self.terminate_download_thread_flag = threading.Event()
            self.download_thread.start()

    def download_videos(self,
                        videos_to_download: list):
        # Need to run the child with Popen so that we can kill it if the main thread dies
        for feed_item in videos_to_download:
            logging.info("Downloading %s" % feed_item.name)
            leafname_pattern = feed_item.id + '.%(ext)s'
            cmd = [self.youtube_dl,
                   '--quiet',
                   '--output', self.config.video_cache_directory / leafname_pattern,
                   '--download-archive', os.devnull,
                   feed_item.url]
            self.child_process = subprocess.Popen(cmd)
            self.active_download_id = feed_item.id
            rtn = self.child_process.wait()
            self.active_download_id = None
            if rtn == 0:
                # download successful
                self._init_download_cache(feed_item)
            self.child_process = None
            if self.terminate_download_thread_flag.is_set():
                break

    def stop_download(self):
        if self.child_process:
            self.terminate_download_thread_flag.set()
            self.child_process.kill()
