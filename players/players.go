package players

import (
	"log"
	"nsw42/picave/profile"

	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type Player interface {
	PlayerState() PlayerState
	Stop()
	PlayPause()
}

type MusicPlayer interface {
	Player
	Play(file string)
}

type VideoPlayer interface {
	Player
	Play(file string, parent *gtk.Widget) *gtk.Widget
}

type PlayerState int

const (
	PlayerNotStarted PlayerState = iota
	PlayerPlaying
	PlayerPaused
	PlayerFinished
)

// This seems like generics should allow us to avoid the duplication,
// but the compiler didn't like it

type MusicPlayerCreator func(*profile.Profile) MusicPlayer

var MusicPlayerLookup = map[string]MusicPlayerCreator{}

func registerMusicPlayer(playerName string, creator MusicPlayerCreator) {
	MusicPlayerLookup[playerName] = creator
}

func CreateMusicPlayerForExt(profile *profile.Profile, ext string) MusicPlayer {
	player, ok := profile.FiletypePlayers[ext]
	if !ok || player == nil {
		log.Println("No known player for files of type " + ext)
		return nil
	}
	playerCreator, ok := MusicPlayerLookup[player.Name]
	if !ok || playerCreator == nil {
		log.Println("Player lookup failed for " + player.Name)
		return nil
	}
	return playerCreator(profile)
}

type VideoPlayerCreator func(*profile.Profile, *profile.FiletypePlayerOptions) VideoPlayer

var VideoPlayerLookup = map[string]VideoPlayerCreator{}

func registerVideoPlayer(playerName string, creator VideoPlayerCreator) {
	VideoPlayerLookup[playerName] = creator
}

func CreateVideoPlayerForExt(profile *profile.Profile, ext string) VideoPlayer {
	player, ok := profile.FiletypePlayers[ext]
	if !ok || player == nil {
		log.Println("No known player for files of type " + ext)
		return nil
	}
	playerCreator, ok := VideoPlayerLookup[player.Name]
	if !ok || playerCreator == nil {
		log.Println("Player lookup failed for " + player.Name)
		return nil
	}
	return playerCreator(profile, player)
}
