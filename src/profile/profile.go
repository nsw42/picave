package profile

import (
	"fmt"
	"nsw42/picave/musicdir"
	"slices"
	"strconv"
)

type Profile struct {
	FilePath            string
	VideoCacheDirectory string
	WarmUpMusic         *musicdir.MusicDirectory
	Executables         map[string]*Executable            // map from player name (e.g. "mpv") to information about the player exe
	FiletypePlayers     map[string]*FiletypePlayerOptions // map from suffix (".mp3") to player name ("mpv") and associated options
	Favourites          []string
	ShowFavouritesOnly  bool
	PowerLevels         map[string]PowerLevels // map from video id (incl DefaultVideoId) to power levels
}

type Executable struct {
	Name           string
	ConfiguredPath string
}

type Margins struct {
	Left   int
	Right  int
	Top    int
	Bottom int
}

type FiletypePlayerOptions struct {
	Name    string // e.g. "mpv"
	Options []string
	Margins Margins
}

// Power level types and constants

type PowerLevels struct {
	Max MaxPowerLevel
	FTP int
}

type MaxPowerLevel struct {
	ValueType  PowerLevelType
	Absolute   int
	PercentFTP int
}

type PowerLevelType int

const (
	NoValue PowerLevelType = iota
	AbsoluteValue
	RelativeToFTPValue
)

const (
	DefaultVideoId = "default"
)

// Profile file JSON keys
const (
	fileKeyVideoCacheDirectory  = "video_cache_directory"
	fileKeyWarmUpMusicDirectory = "warm_up_music_directory"
	fileKeyExecutables          = "executables"
	fileKeyExePath              = "path"
	fileKeyFiletypes            = "filetypes"
	fileKeyPlayer               = "player"
	fileKeyOptions              = "options"
	fileKeyParameters           = "parameters"
	fileKeyParamMarginLeft      = "margin_left"
	fileKeyParamMarginRight     = "margin_right"
	fileKeyParamMarginTop       = "margin_top"
	fileKeyParamMarginBottom    = "margin_bottom"
	fileKeyFavourites           = "favourites"
	fileKeyShowFavouritesOnly   = "show_favourites_only"
	fileKeyPowerLevels          = "power_levels"
	fileKeyFTP                  = "FTP"
	fileKeyMax                  = "MAX"
)

func (profile *Profile) DefaultFTP() string {
	return profile.GetVideoFTP(DefaultVideoId, false)
}

func (profile *Profile) DefaultFTPVal() int {
	return profile.GetVideoFTPVal(DefaultVideoId, false)
}

func (profile *Profile) SetDefaultFTPVal(ftp int) {
	// stupid language
	powerLevel := profile.PowerLevels[DefaultVideoId]
	powerLevel.FTP = ftp
	profile.PowerLevels[DefaultVideoId] = powerLevel
}

func (profile *Profile) DefaultMax() string {
	return profile.GetVideoMax(DefaultVideoId, false)
}

func (profile *Profile) DefaultMaxVal() int {
	return profile.GetVideoMaxVal(DefaultVideoId, false)
}

func (profile *Profile) GetVideoFTP(videoId string, expandDefault bool) string {
	val := profile.GetVideoFTPVal(videoId, expandDefault)
	if val == 0 {
		return ""
	}
	return strconv.Itoa(val)
}

func (profile *Profile) GetVideoFTPVal(videoId string, expandDefault bool) int {
	val, found := profile.PowerLevels[videoId]
	if found && val.FTP != 0 {
		return val.FTP
	}
	if expandDefault {
		return profile.DefaultFTPVal()
	}
	return 0
}

func (profile *Profile) GetVideoMax(videoId string, expandDefault bool) string {
	val, found := profile.PowerLevels[videoId]
	if found {
		max := val.Max
		switch max.ValueType {
		case NoValue:
			return ""
		case AbsoluteValue:
			return strconv.Itoa(max.Absolute)
		case RelativeToFTPValue:
			return fmt.Sprintf("%d%%", max.PercentFTP)
		}
	}
	if expandDefault {
		return profile.GetVideoMax(DefaultVideoId, false)
	}
	return ""
}

func (profile *Profile) GetVideoMaxVal(videoId string, expandDefault bool) int {
	val, found := profile.PowerLevels[videoId]
	if found {
		max := val.Max
		switch max.ValueType {
		case NoValue:
			return 0
		case AbsoluteValue:
			return max.Absolute
		case RelativeToFTPValue:
			ftp := profile.GetVideoFTPVal(videoId, expandDefault)
			return ftp * max.PercentFTP / 100.0
		}
	}
	if expandDefault {
		return profile.GetVideoMaxVal(DefaultVideoId, false)
	}
	return 0
}

func (profile *Profile) SetVideoFTPDefault(videoId string) {
	profile.SetVideoFTPVal(videoId, 0)
}

func (profile *Profile) SetVideoFTPVal(videoId string, ftp int) {
	profile.PowerLevels[videoId] = PowerLevels{
		Max: profile.PowerLevels[videoId].Max,
		FTP: ftp,
	}
}

func (profile *Profile) SetVideoMaxDefault(videoId string) {
	profile.SetVideoMaxVal(videoId, MaxPowerLevel{NoValue, 0, 0})
}

func (profile *Profile) SetVideoMaxAbsolute(videoId string, absolute int) {
	profile.SetVideoMaxVal(videoId, MaxPowerLevel{AbsoluteValue, absolute, 0})
}

func (profile *Profile) SetVideoMaxRelative(videoId string, relative int) {
	profile.SetVideoMaxVal(videoId, MaxPowerLevel{RelativeToFTPValue, 0, relative})
}

func (profile *Profile) SetVideoMaxVal(videoId string, level MaxPowerLevel) {
	profile.PowerLevels[videoId] = PowerLevels{
		Max: level,
		FTP: profile.PowerLevels[videoId].FTP,
	}
}

func (profile *Profile) ToggleVideoFavourite(videoId string) {
	index := slices.Index(profile.Favourites, videoId)
	if index == -1 {
		profile.Favourites = append(profile.Favourites, videoId)
	} else {
		profile.Favourites = slices.Delete(profile.Favourites, index, index+1)
	}
}
