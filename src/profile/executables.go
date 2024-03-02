package profile

import (
	"errors"
	"os"
	"os/exec"
)

const (
	ExeNameYoutubeDL = "youtube-dl"
	ExeNameYTDLP     = "yt-dlp"
)

func NewExecutable(exeName string, configuredPath string) *Executable {
	return &Executable{exeName, configuredPath}
}

func (executable *Executable) ExePath() string {
	var exePath string
	var err error
	if executable.ConfiguredPath == "" {
		exePath, err = exec.LookPath(executable.Name)
		if err == nil {
			// We found it
			return exePath
		}
		if executable.Name == ExeNameYoutubeDL {
			// Try its alternatives
			exePath, err = exec.LookPath(ExeNameYTDLP)
			if err == nil {
				return exePath
			}
		}
		return ""
	} else {
		_, err = os.Stat(executable.ConfiguredPath)
		if errors.Is(err, os.ErrNotExist) || errors.Is(err, os.ErrPermission) {
			return ""
		}
		return executable.ConfiguredPath
	}
}
