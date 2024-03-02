package players

import (
	"fmt"
	"log"
	"nsw42/picave/profile"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/diamondburned/gotk4/pkg/gtk/v4"
	"golang.org/x/sys/unix"
)

const (
	MplayerFifoName = "/tmp/picave.mplayer-fifo"
)

type MplayerPlayer struct {
	State   PlayerState
	Profile *profile.Profile
	Command *exec.Cmd
}

func NewMplayerPlayer(profile *profile.Profile, options *profile.FiletypePlayerOptions) VideoPlayer {
	return &MplayerPlayer{PlayerNotStarted, profile, nil}
}

func (player *MplayerPlayer) PlayerState() PlayerState {
	return player.State
}

func (player *MplayerPlayer) Play(file string, parent *gtk.Widget) *gtk.Widget {
	exe := player.Profile.Executables["mplayer"].ExePath()
	if exe == "" {
		log.Println("Unable to find mplayer executable. Skipping playback.")
		return nil
	}
	go player.launch(exe, file)
	return nil
}

func (player *MplayerPlayer) PlayPause() {
	player.sendCommand("pause")
}

func (player *MplayerPlayer) sendCommand(command string) {
	handle, err := os.OpenFile(MplayerFifoName, os.O_WRONLY, os.ModeAppend)
	if err != nil {
		log.Println("Unable to open mplayer FIFO", err)
		return
	}
	defer handle.Close()
	_, err = fmt.Fprintln(handle, command)
	if err != nil {
		log.Println("Failed writing to FIFO", err)
		return
	}

	if player.State == PlayerPlaying {
		player.State = PlayerPaused
	} else {
		player.State = PlayerPlaying
	}
}

func (player *MplayerPlayer) Stop() {
	if player.Command != nil {
		player.Command.Process.Kill()
	}
}

func (player *MplayerPlayer) launch(exe string, file string) {
	os.Remove(MplayerFifoName)
	if err := unix.Mkfifo(MplayerFifoName, 0666); err != nil {
		log.Println("Unable to create fifo")
		return
	}
	opts := player.Profile.FiletypePlayers[filepath.Ext(file)].Options
	if len(opts) == 0 {
		opts = []string{
			"-geometry", "0:0",
			"-ontop",
		}
	}
	allOpts := append(opts, "-slave")
	allOpts = append(allOpts, "-input")
	allOpts = append(allOpts, "file="+MplayerFifoName)
	allOpts = append(allOpts, file)
	player.Command = exec.Command(exe, allOpts...)
	player.State = PlayerPlaying
	player.Command.Run()
	player.State = PlayerFinished
}

func init() {
	registerVideoPlayer("mplayer", NewMplayerPlayer)
}
