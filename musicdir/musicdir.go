package musicdir

import (
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
)

type MusicDirectory struct {
	BasePath string
	Files    []string // All files are relative to BasePath, to reduce memory usage
}

func FindMusicFiles(directory string) *MusicDirectory {
	// Return a list of (absolute path of) all music files in the given directory
	rtn := &MusicDirectory{directory, []string{}}
	traverse(directory, "", rtn)
	return rtn
}

func traverse(absolutePath string, relativePath string, md *MusicDirectory) {
	files, err := os.ReadDir(absolutePath)
	if err != nil {
		fmt.Println("Failed traversing ", absolutePath, " (", relativePath, ")")
		return
	}
	for _, file := range files {
		fileRelPath := filepath.Join(relativePath, file.Name())
		if file.IsDir() {
			subdir := filepath.Join(absolutePath, file.Name())
			traverse(subdir, fileRelPath, md)
		} else {
			switch filepath.Ext(file.Name()) {
			case ".mp3", ".mp4", ".m4a":
				md.Files = append(md.Files, fileRelPath)
			}
		}
	}
}

func (musicDir *MusicDirectory) PickRandomFile() string {
	file := rand.Intn(len(musicDir.Files))
	return filepath.Join(musicDir.BasePath, musicDir.Files[file])
}
