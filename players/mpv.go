package players

import (
	"nsw42/picave/profile"
	"os/exec"
	"path/filepath"
)

type MpvPlayer struct {
	Profile         *profile.Profile
	Command         *exec.Cmd
	CommandFinished bool
	IpcAddress      string
}

func (player *MpvPlayer) IsFinished() bool {
	return player.CommandFinished
}

func (player *MpvPlayer) Play(file string) {
	exe := player.Profile.Executables["mpv"]
	go player.launch(exe, file)
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
			"--input-ipc-server=" + player.IpcAddress,
		}
	}
	allOpts := append([]string{}, file)
	allOpts = append(allOpts, opts...)
	player.CommandFinished = false
	player.Command = exec.Command(exe, allOpts...)
	player.Command.Run()
	player.CommandFinished = true
}

func NewMpvPlayer(profile *profile.Profile) Player {
	return &MpvPlayer{profile, nil, false, "/tmp/picave.mpv-socket"}
}

func init() {
	registerPlayer("mpv", NewMpvPlayer)
}
