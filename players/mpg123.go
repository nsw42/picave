package players

import (
	"fmt"
	"nsw42/picave/profile"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/creack/pty"
)

type Mpg123Player struct {
	Profile  *profile.Profile
	Command  *exec.Cmd
	ChildPty *os.File
	State    PlayerState
}

func (player *Mpg123Player) PlayerState() PlayerState {
	return player.State
}

func (player *Mpg123Player) Play(file string) {
	exe := player.Profile.Executables["mpg123"]
	go player.launch(exe, file)
}

func (player *Mpg123Player) PlayPause() {
	// Based on https://stackoverflow.com/questions/17416158/python-2-7-subprocess-control-interaction-with-mpg123
	if player.ChildPty == nil {
		fmt.Println("No pipe for child")
		return
	}
	n, err := player.ChildPty.Write([]byte{'s'})
	if err != nil || n == 0 {
		fmt.Println("Failed writting to child pipe: ", err.Error())
		return
	}
	if player.State == PlayerPlaying {
		player.State = PlayerPaused
	} else {
		player.State = PlayerPlaying
	}
}

func (player *Mpg123Player) Stop() {
	if player.Command != nil {
		player.Command.Process.Kill()
	}
}

func (player *Mpg123Player) launch(exe string, file string) {
	opts := player.Profile.FiletypePlayers[filepath.Ext(file)].Options
	if len(opts) == 0 {
		opts = []string{
			"--quiet",
		}
	}
	allOpts := []string{file}
	allOpts = append(allOpts, opts...)
	allOpts = append(allOpts, "--control")
	player.State = PlayerPlaying
	player.Command = exec.Command(exe, allOpts...)
	pty, err := pty.Start(player.Command)
	if err == nil {
		player.ChildPty = pty
	}
	player.Command.Wait()
	player.State = PlayerFinished
}

func NewMpg123Player(profile *profile.Profile) Player {
	return &Mpg123Player{profile, nil, nil, PlayerNotStarted}
}

func init() {
	registerPlayer("mpg123", NewMpg123Player)
}
