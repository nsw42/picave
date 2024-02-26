package profilechooser

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type CompletionCallback func(string)

type ProfileChooserWindow struct {
	*gtk.ApplicationWindow
	MruFilename        string
	Mru                []MruEntry
	CompletionCallback CompletionCallback
}

type MruEntry struct {
	DisplayName string
	ProfilePath string
}

const (
	MruLeafname = ".picaverc.mru"
)

func NewProfileChooserWindow(app *gtk.Application, selectProfilePath string, completionCallback CompletionCallback) *ProfileChooserWindow {
	toSelectAbs, err := filepath.Abs(selectProfilePath)
	if err != nil {
		toSelectAbs = selectProfilePath
	}
	rtn := &ProfileChooserWindow{}
	rtn.ApplicationWindow = gtk.NewApplicationWindow(app)
	rtn.ApplicationWindow.SetTitle("PiCave profile chooser")
	homedir, err := os.UserHomeDir()
	if err != nil {
		rtn.MruFilename = MruLeafname
	} else {
		rtn.MruFilename = filepath.Join(homedir, MruLeafname)
	}
	rtn.Mru = tryLoadMru(rtn.MruFilename)
	rtn.CompletionCallback = completionCallback

	layout := gtk.NewBox(gtk.OrientationVertical, 4)
	layout.SetHomogeneous(false)
	// List of existing items
	listbox := gtk.NewListBox()
	for _, mruitem := range rtn.Mru {
		listboxrow := gtk.NewListBoxRow()
		listboxrow.SetChild(gtk.NewLabel(mruitem.DisplayName))
		listbox.Append(listboxrow)
		mruPathAbs, err := filepath.Abs(mruitem.ProfilePath)
		if err != nil {
			mruPathAbs = mruitem.ProfilePath
		}
		if mruPathAbs == toSelectAbs {
			listbox.SelectRow(listboxrow)
		}
	}
	listbox.SetVExpand(true)
	listbox.ConnectRowActivated(rtn.OnProfileChosen)
	layout.Append(listbox)

	layout.SetMarginStart(100)
	layout.SetMarginEnd(100)
	layout.SetMarginTop(50)
	layout.SetMarginBottom(50)
	rtn.SetChild(layout)

	rtn.ConnectRealize(func() {
		rtn.SetSizeRequest(640, 480)
	})

	return rtn
}

func (window *ProfileChooserWindow) OnProfileChosen(row *gtk.ListBoxRow) {
	// TODO: Ensure the OnClose handler doesn't trigger
	window.CompletionCallback(window.Mru[row.Index()].ProfilePath)
	window.Close()
}

func tryLoadMru(filename string) []MruEntry {
	data, err := os.ReadFile(filename)
	if err != nil {
		return []MruEntry{}
	}
	var stringArray [][]string
	err = json.Unmarshal(data, &stringArray)
	if err != nil {
		fmt.Println("Warning: Unable to read MRU file", filename, ":", err)
		return []MruEntry{}
	}
	mru := []MruEntry{}
	for _, strings := range stringArray {
		if len(strings) != 2 {
			fmt.Println("Warning; Invalid MRU file format in ", filename)
			return []MruEntry{}
		}
		mru = append(mru, MruEntry{strings[0], strings[1]})
	}

	return mru
}
