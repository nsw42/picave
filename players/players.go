package players

import (
	"fmt"
	"nsw42/picave/profile"
)

type Player interface {
	PlayerState() PlayerState
	Play(file string)
	Stop()
	PlayPause()
}

type PlayerState int

const (
	PlayerNotStarted PlayerState = iota
	PlayerPlaying
	PlayerPaused
	PlayerFinished
)

type PlayerCreator func(*profile.Profile) Player

var PlayerLookup = make(map[string]PlayerCreator, 0)

func CreatePlayerForExt(profile *profile.Profile, ext string) Player {
	player, ok := profile.FiletypePlayers[ext]
	if !ok || player == nil {
		fmt.Println("No known player for files of type " + ext)
		return nil
	}
	playerCreator, ok := PlayerLookup[player.Name]
	if !ok || playerCreator == nil {
		fmt.Println("Player lookup failed for " + player.Name)
		return nil
	}
	return playerCreator(profile)
}

func registerPlayer(playerName string, creator PlayerCreator) {
	PlayerLookup[playerName] = creator
}
