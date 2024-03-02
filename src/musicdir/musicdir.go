package musicdir

import (
	"log"
	"math/rand"
	"os"
	"path/filepath"
)

type MusicDirectory struct {
	BasePath string
	Exists   bool
	Files    []string // All files are relative to BasePath, to reduce memory usage
}

func NewMusicDirectory(directory string) *MusicDirectory {
	// Return a list of (absolute path of) all music files in the given directory
	rtn := &MusicDirectory{directory, false, []string{}}
	rtn.Refresh()
	return rtn
}

func (musicDir *MusicDirectory) PickRandomFile() string {
	file := rand.Intn(len(musicDir.Files))
	return filepath.Join(musicDir.BasePath, musicDir.Files[file])
}

func (musicDir *MusicDirectory) Refresh() {
	musicDir.Files = []string{}
	musicDir.Exists = musicDir.traverse(musicDir.BasePath, "")
}

func (musicDir *MusicDirectory) traverse(absolutePath string, relativePath string) bool {
	// Returns true if the given directory exists; false otherwise
	files, err := os.ReadDir(absolutePath)
	if err != nil {
		log.Println("Failed traversing ", absolutePath, " (", relativePath, ")")
		return false
	}
	for _, file := range files {
		fileRelPath := filepath.Join(relativePath, file.Name())
		if file.IsDir() {
			subdir := filepath.Join(absolutePath, file.Name())
			musicDir.traverse(subdir, fileRelPath)
		} else {
			switch filepath.Ext(file.Name()) {
			case ".mp3", ".mp4", ".m4a":
				musicDir.Files = append(musicDir.Files, fileRelPath)
			}
		}
	}
	return true
}
