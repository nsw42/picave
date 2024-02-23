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
	State    PlayerState
	Profile  *profile.Profile
	Command  *exec.Cmd
	ChildPty *os.File
}

func NewMpg123Player(profile *profile.Profile) MusicPlayer {
	return &Mpg123Player{PlayerNotStarted, profile, nil, nil}
}

func init() {
	registerMusicPlayer("mpg123", NewMpg123Player)
}

func (player *Mpg123Player) PlayerState() PlayerState {
	return player.State
}

func (player *Mpg123Player) Play(file string) {
	go player.launch(file)
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

func (player *Mpg123Player) launch(file string) {
	exe := player.Profile.Executables["mpg123"].ExePath()
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
