package players

import (
	"nsw42/picave/profile"
	"os/exec"
)

type Mpg123Player struct {
	Profile         *profile.Profile
	Command         *exec.Cmd
	CommandFinished bool
}

func (player *Mpg123Player) IsFinished() bool {
	return player.CommandFinished
}

func (player *Mpg123Player) Play(file string) {
	exe := player.Profile.Executables["mpg123"]
	go player.launch(exe, file)
}

func (player *Mpg123Player) Stop() {
	if player.Command != nil {
		player.Command.Process.Kill()
	}
}

func (player *Mpg123Player) launch(exe string, file string) {
	player.CommandFinished = false
	player.Command = exec.Command(exe, file)
	player.Command.Run()
	player.CommandFinished = true
}

func NewMpg123Player(profile *profile.Profile) Player {
	return &Mpg123Player{profile, nil, false}
}

func init() {
	registerPlayer("mpg123", NewMpg123Player)
}
