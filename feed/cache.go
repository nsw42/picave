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
	State           map[string]DownloadState
	Path            map[string]string
	DownloadCommand *exec.Cmd
	DownloadContext context.Context
	CancelDownload  context.CancelFunc
}

func lookForVideo(profile *profile.Profile, itemId string) (string, DownloadState) {
	// Returns path and download state
	if profile.VideoCacheDirectory == "" {
		return "", DownloadBlocked
	}
	matches, err := filepath.Glob(filepath.Join(profile.VideoCacheDirectory, itemId+".*"))
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
	cache := &FeedCache{}
	cache.State = map[string]DownloadState{}
	cache.Path = map[string]string{}
	ctx := context.Background()
	cache.DownloadContext, cache.CancelDownload = context.WithCancel(ctx)
	for _, item := range Index {
		cache.Path[item.Id], cache.State[item.Id] = lookForVideo(profile, item.Id)
	}
	go cache.StartDownloads(profile)
	return cache
}

func (cache *FeedCache) StartDownloads(profile *profile.Profile) {
	downloadItemChannel := make(chan int)
	go cache.DoDownloads(profile, downloadItemChannel)
	for itemIndex, item := range Index {
		if cache.State[item.Id] == NotDownloaded {
			downloadItemChannel <- itemIndex
		}
	}
}

func (cache *FeedCache) DoDownloads(profile *profile.Profile, itemIndexChan chan int) {
	ytdlp := profile.Executables["youtube-dl"].ExePath()
	if ytdlp == "" {
		log.Println("No path configured for youtube-dl, and unable to find it on the PATH. Download not possible.")
		return
	}
	cacheDir := profile.VideoCacheDirectory // Guaranteed not empty if we're actually going to use it: cache.State[itemId] = DownloadBlocked if there's no cache dir
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
				cache.Path[item.Id], cache.State[item.Id] = lookForVideo(profile, item.Id)
			}
			cache.DownloadCommand = nil
		}
	}
}

func (cache *FeedCache) StopUpdating() {
	cache.CancelDownload()
	if cache.DownloadCommand != nil {
		cache.DownloadCommand.Process.Kill()
	}
}
