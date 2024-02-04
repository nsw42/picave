package feed

import (
	"nsw42/picave/profile"
	"path/filepath"
)

type DownloadState int

const (
	NotDownloaded = iota
	Downloading
	Downloaded
)

type FeedCache struct {
	// all cache items are indexed by video id
	State map[string]DownloadState
	Path  map[string]string
}

func NewFeedCache(profile *profile.Profile) *FeedCache {
	cache := &FeedCache{}
	cache.State = map[string]DownloadState{}
	cache.Path = map[string]string{}
	for _, item := range Index {
		cache.Path[item.Id] = lookForVideo(profile, item.Id)
		if cache.Path[item.Id] == "" {
			cache.State[item.Id] = NotDownloaded
		} else {
			cache.State[item.Id] = Downloaded
		}
	}
	return cache
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
