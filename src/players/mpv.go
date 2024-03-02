package players

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"nsw42/picave/profile"
	"os/exec"
	"path/filepath"

	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

var pauseCommand []byte
var resumeCommand []byte

type MpvPlayer struct {
	Profile    *profile.Profile
	Command    *exec.Cmd
	IpcAddress string
	State      PlayerState
	Socket     net.Conn
}

func (player *MpvPlayer) PlayerState() PlayerState {
	return player.State
}

func (player *MpvPlayer) Play(file string, parent *gtk.Widget) *gtk.Widget {
	exe := player.Profile.Executables["mpv"].ExePath()
	if exe == "" {
		fmt.Println("Unable to find mpv executable. Skipping playback.")
		return nil
	}
	go player.launch(exe, file)
	return nil
}

func (player *MpvPlayer) PlayPause() {
	switch player.State {
	case PlayerPlaying:
		player.sendCommand(pauseCommand)
		player.State = PlayerPaused
	case PlayerPaused:
		player.sendCommand(resumeCommand)
		player.State = PlayerPlaying
	}
}

func (player *MpvPlayer) sendCommand(command []byte) {
	if player.Socket == nil {
		socket, err := net.Dial("unix", player.IpcAddress)
		if err != nil {
			log.Println("Unable to create socket to connect to " + player.IpcAddress)
			return
		}
		player.Socket = socket
	}
	n, err := player.Socket.Write(command)
	if err != nil {
		log.Println("Failed to write to socket: " + err.Error())
		return
	}
	if n < len(command) {
		log.Println("Truncated write to socket:", n, "of", len(command))
		return
	}
}

func (player *MpvPlayer) Stop() {
	if player.Command != nil {
		player.Command.Process.Kill()
	}
}

func (player *MpvPlayer) launch(exe string, file string) {
	opts := player.Profile.FiletypePlayers[filepath.Ext(file)].Options
	if len(opts) == 0 {
		opts = []string{
			"--geometry=0:0",
			"--ontop",
		}
	}
	allOpts := []string{file}
	allOpts = append(allOpts, opts...)
	allOpts = append(allOpts, "--input-ipc-server="+player.IpcAddress)
	player.Command = exec.Command(exe, allOpts...)
	player.State = PlayerPlaying
	player.Command.Run()
	player.State = PlayerFinished
}

func NewMpvPlayer(profile *profile.Profile, options *profile.FiletypePlayerOptions) VideoPlayer {
	return &MpvPlayer{profile, nil, "/tmp/picave.mpv-socket", PlayerNotStarted, nil}
}

func encodeCommand(command []string) []byte {
	toEncode := map[string][]string{"command": command}
	marshalled, err := json.Marshal(toEncode)
	if err != nil {
		panic("Unable to marshal command: " + fmt.Sprintf("%v", toEncode))
	}
	marshalled = append(marshalled, '\n')
	return marshalled
}

func init() {
	pauseCommand = encodeCommand([]string{"set_property_string", "pause", "yes"})
	resumeCommand = encodeCommand([]string{"set_property_string", "pause", "no"})
	registerVideoPlayer("mpv", NewMpvPlayer)
}
