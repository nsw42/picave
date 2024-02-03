package players

import "nsw42/picave/profile"

type Player interface {
	IsFinished() bool
	Play(file string)
	Stop()
}

type PlayerCreator func(*profile.Profile) Player

var PlayerLookup = make(map[string]PlayerCreator, 0)

func registerPlayer(playerName string, creator PlayerCreator) {
	PlayerLookup[playerName] = creator
}
