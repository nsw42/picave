package feed

import (
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
}

func lookForYoutubeDL() string {
	ytdlp, err := exec.LookPath("youtube-dl")
	if err != nil {
		ytdlp, err = exec.LookPath("yt-dlp")
	}
	if err != nil {
		return ""
	}
	return ytdlp
}

func lookForVideo(profile *profile.Profile, itemId string) string {
	matches, err := filepath.Glob(filepath.Join(profile.VideoCacheDirectory, itemId+".*"))
	if err != nil {
		return ""
	}
	for _, match := range matches {
		switch filepath.Ext(match) {
		case ".mp4", ".mkv":
			return match
		}
	}
	return ""
}

func NewFeedCache(profile *profile.Profile) *FeedCache {
	cache := &FeedCache{}
	cache.State = map[string]DownloadState{}
	cache.Path = map[string]string{}
	downloadNeeded := false
	for _, item := range Index {
		cache.Path[item.Id] = lookForVideo(profile, item.Id)
		state := NotDownloaded // Unless we decide otherwise
		if cache.Path[item.Id] != "" {
			if fileinfo, err := os.Stat(cache.Path[item.Id]); err == nil {
				if fileinfo.Size() < 100 {
					state = DownloadBlocked
				} else {
					state = Downloaded
				}
			}
		}
		cache.State[item.Id] = state
		if state == NotDownloaded {
			downloadNeeded = true
		}
	}
	if downloadNeeded {
		go cache.StartDownload(profile)
	}
	return cache
}

func (cache *FeedCache) StartDownload(profile *profile.Profile) {
	ytdlp := profile.Executables["youtube-dl"]
	if ytdlp == "" {
		ytdlp = lookForYoutubeDL()
		if ytdlp == "" {
			log.Println("No path configured for youtube-dl, and unable to find it on the PATH. Download not possible.")
			return
		}
	}
	cacheDir := profile.VideoCacheDirectory
	for _, item := range Index {
		if cache.State[item.Id] == Downloaded || cache.State[item.Id] == DownloadBlocked {
			continue
		}
		cache.DownloadCommand = exec.Command(ytdlp,
			"--quiet",
			"--output", cacheDir+"/"+item.Id+".%(ext)s",
			"--download-archive", "/dev/null",
			item.Url)
		cache.State[item.Id] = Downloading
		err := cache.DownloadCommand.Run()
		newState := NotDownloaded // Unless we find it
		if err == nil {
			// Download (presumably) successful
			cache.Path[item.Id] = lookForVideo(profile, item.Id)
			if cache.Path[item.Id] != "" {
				newState = Downloaded
			}
		}
		cache.State[item.Id] = newState
	}
}
