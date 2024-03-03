package players

import (
	"fmt"
	"nsw42/picave/profile"
	"os/exec"
	"path/filepath"
	"strconv"

	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type FfplayPlayer struct {
	Profile *profile.Profile
	Command *exec.Cmd
	State   PlayerState
}

func NewFfplayPlayer(profile *profile.Profile, options *profile.FiletypePlayerOptions) VideoPlayer {
	return &FfplayPlayer{profile, nil, PlayerNotStarted}
}

func (player *FfplayPlayer) PlayerState() PlayerState {
	return player.State
}

func (player *FfplayPlayer) Play(file string, parent *gtk.Widget) *gtk.Widget {
	exe := player.Profile.Executables["ffplay"]
	if exe == nil || exe.ExePath() == "" {
		fmt.Println("Unable to find ffplay executable. Skipping playback.")
		return nil
	}
	player.State = PlayerNotStarted
	go player.launch(exe.ExePath(), file, parent.AllocatedWidth(), parent.AllocatedHeight())
	return nil
}

func (player *FfplayPlayer) PlayPause() {
	fmt.Println("Play/Pause not supported for ffplay: it only accepts keypresses in its window")
}

func (player *FfplayPlayer) Stop() {
	if player.Command != nil {
		player.Command.Process.Kill()
	}
}

func (player *FfplayPlayer) launch(exe string, file string, width, height int) {
	opts := player.Profile.FiletypePlayers[filepath.Ext(file)].Options
	if len(opts) == 0 {
		opts = []string{
			"-alwaysontop",
			"-autoexit",
			"-left", "0",
			"-top", "0",
		}
	}
	allOpts := append(opts,
		"-x", strconv.Itoa(width),
		"-y", strconv.Itoa(height),
		file)
	player.Command = exec.Command(exe, allOpts...)
	player.State = PlayerPlaying
	player.Command.Run()
	player.State = PlayerFinished
}

func init() {
	registerVideoPlayer("ffplay", NewFfplayPlayer)
}
