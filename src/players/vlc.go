//go:build ignore

package players

import (
	"log"
	"nsw42/picave/profile"
	"os/exec"

	vlc "github.com/adrg/libvlc-go/v3"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

func init() {
	if err := vlc.Init(); err != nil {
		log.Fatal(err)
	}
	// vlc.Release?
}

type VlcPlayer struct {
	State   PlayerState
	Profile *profile.Profile
	Command *exec.Cmd
	Vlc     *vlc.Player
}

func NewVlcPlayer(profile *profile.Profile) Player {
	return &VlcPlayer{PlayerNotStarted, profile, nil, nil}
}

func init() {
	registerPlayer("vlc", NewVlcPlayer)
}

func (player *VlcPlayer) PlayerState() PlayerState {
	return player.State
}

func (player *VlcPlayer) Play(file string) {
	// TODO
}

func (player *VlcPlayer) PlayVideo(file string, drawingAreea *gtk.DrawingArea) {
	go player.launch(file, drawingAreea)
}

func (player *VlcPlayer) PlayPause() {
	if player.Vlc != nil {
		player.Vlc.TogglePause()
	}
}

func (player *VlcPlayer) Stop() {
	if player.Vlc != nil {
		player.Vlc.Stop()
	}
}

func (player *VlcPlayer) launch(file string, drawingArea *gtk.DrawingArea) {
	surface := drawingArea.Native().Surface()
	vlcPlayer, err := vlc.NewPlayer()
	if err != nil {
		log.Println("Unable to launch VLC")
		player.State = PlayerFinished
		return
	}
	player.Vlc = vlcPlayer
	media, err := vlcPlayer.LoadMediaFromPath(file)
	if err != nil {
		log.Println("Unable to open media " + file)
		player.State = PlayerFinished
		return
	}
	defer media.Release()

	player.State = PlayerPlaying
	vlcPlayer.Play()
	player.State = PlayerFinished
}
