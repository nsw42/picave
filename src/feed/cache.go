package feed

import (
	"context"
	"log"
	"nsw42/picave/profile"
	"os"
	"os/exec"
	"path/filepath"
)

type DownloadState int

const (
	NotDownloaded DownloadState = iota
	DownloadBlocked
	Downloading
	Downloaded
)

type FeedCache struct {
	// all cache items are indexed by video id
	Profile         *profile.Profile
	BaseDirExists   bool
	State           map[string]DownloadState
	Path            map[string]string
	DownloadCommand *exec.Cmd
	DownloadContext context.Context
	CancelDownload  context.CancelFunc
}

func (cache *FeedCache) lookForVideo(itemId string) (string, DownloadState) {
	// Returns path and download state
	if !cache.BaseDirExists {
		return "", DownloadBlocked
	}
	matches, err := filepath.Glob(filepath.Join(cache.Profile.VideoCacheDirectory, itemId+".*"))
	if err != nil {
		return "", NotDownloaded
	}
	for _, match := range matches {
		switch filepath.Ext(match) {
		case ".mp4", ".mkv":
			if fileinfo, err := os.Stat(match); err == nil {
				if fileinfo.Size() < 1024 {
					return match, DownloadBlocked
				} else {
					return match, Downloaded
				}
			}
			return match, NotDownloaded
		}
	}
	return "", NotDownloaded
}

func NewFeedCache(profile *profile.Profile) *FeedCache {
	cache := &FeedCache{Profile: profile}
	cache.Refresh()
	ctx := context.Background()
	cache.DownloadContext, cache.CancelDownload = context.WithCancel(ctx)
	return cache
}

func (cache *FeedCache) Refresh() {
	// Check whether the configured video cache directory now exists, and start downloading if it does.
	cache.BaseDirExists = false
	if stat, err := os.Stat(cache.Profile.VideoCacheDirectory); err == nil {
		if stat.IsDir() {
			cache.BaseDirExists = true
		}
	}
	cache.State = map[string]DownloadState{}
	cache.Path = map[string]string{}
	for _, item := range Index {
		cache.Path[item.Id], cache.State[item.Id] = cache.lookForVideo(item.Id) // Ensure we set DownloadBlocked for every video if the VideoCacheDirectory doesn't exist
	}
	if cache.BaseDirExists {
		go cache.StartDownloads()
	}
}

func (cache *FeedCache) StartDownloads() {
	downloadItemChannel := make(chan int)
	go cache.DoDownloads(downloadItemChannel)
	for itemIndex, item := range Index {
		if cache.State[item.Id] == NotDownloaded {
			downloadItemChannel <- itemIndex
		}
	}
}

func (cache *FeedCache) DoDownloads(itemIndexChan chan int) {
	ytdlp := cache.Profile.Executables["youtube-dl"].ExePath()
	if ytdlp == "" {
		log.Println("No path configured for youtube-dl, and unable to find it on the PATH. Download not possible.")
		return
	}
	cacheDir := cache.Profile.VideoCacheDirectory // *Should* exist by the time we're going to use it: Refresh() only calls StartDownloads once the directory is found (but TOCTOU)
	for {
		select {
		case <-cache.DownloadContext.Done():
			// StopUpdating() has been called
			return
		case itemIndex := <-itemIndexChan:
			item := Index[itemIndex]
			cache.DownloadCommand = exec.Command(ytdlp,
				"--quiet",
				"--output", cacheDir+"/"+item.Id+".%(ext)s",
				"--download-archive", "/dev/null",
				item.Url)
			cache.State[item.Id] = Downloading
			err := cache.DownloadCommand.Run()
			if err == nil {
				// Download (presumably) successful
				cache.Path[item.Id], cache.State[item.Id] = cache.lookForVideo(item.Id)
			}
			cache.DownloadCommand = nil
		}
	}
}

func (cache *FeedCache) StopUpdating() {
	cache.CancelDownload()
	if cache.DownloadCommand != nil {
		cache.DownloadCommand.Process.Kill()
		cache.DownloadCommand = nil
	}
}
