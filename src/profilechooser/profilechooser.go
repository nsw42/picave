package profilechooser

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"

	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type CompletionCallback func(string)

type ProfileChooserWindow struct {
	*gtk.ApplicationWindow
	MruFilename        string
	MruListbox         *gtk.ListBox
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
	rtn.Mru = rtn.TryLoadMru()
	rtn.CompletionCallback = completionCallback

	layout := gtk.NewBox(gtk.OrientationVertical, 4)
	layout.SetHomogeneous(false)
	// List of existing items
	rtn.MruListbox = gtk.NewListBox()
	for _, mruitem := range rtn.Mru {
		mruPathAbs, err := filepath.Abs(mruitem.ProfilePath)
		if err != nil {
			mruPathAbs = mruitem.ProfilePath
		}
		rtn.AddListBoxEntry(mruitem.DisplayName, mruPathAbs == toSelectAbs)
	}
	rtn.MruListbox.SetVExpand(true)
	rtn.MruListbox.ConnectRowActivated(rtn.OnProfileChosen)
	layout.Append(rtn.MruListbox)
	// 'Add' button
	add := gtk.NewButtonWithLabel("Add")
	add.ConnectClicked(rtn.DoAddDialog)
	layout.Append(add)

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

func (window *ProfileChooserWindow) AddListBoxEntry(displayName string, selectItem bool) {
	listboxrow := gtk.NewListBoxRow()
	listboxrow.SetChild(gtk.NewLabel(displayName))
	window.MruListbox.Append(listboxrow)
	if selectItem {
		window.MruListbox.SelectRow(listboxrow)
	}
}

func (window *ProfileChooserWindow) OnProfileChosen(row *gtk.ListBoxRow) {
	window.CompletionCallback(window.Mru[row.Index()].ProfilePath)
	window.Close()
}

// Note that the file format for the MRU was chosen for compatibility with the MRU written by the Python version.
// It might make sense to make TryLoadMru support both, but switch to an object-format at some point in the future.

func (window *ProfileChooserWindow) TryLoadMru() []MruEntry {
	data, err := os.ReadFile(window.MruFilename)
	if err != nil {
		return []MruEntry{}
	}
	var stringArray [][]string
	err = json.Unmarshal(data, &stringArray)
	if err != nil {
		fmt.Println("Warning: Unable to read MRU file", window.MruFilename, ":", err)
		return []MruEntry{}
	}
	mru := []MruEntry{}
	for _, strings := range stringArray {
		if len(strings) != 2 {
			fmt.Println("Warning; Invalid MRU file format in ", window.MruFilename)
			return []MruEntry{}
		}
		mru = append(mru, MruEntry{strings[0], strings[1]})
	}

	return mru
}

func (window *ProfileChooserWindow) SaveMru() {
	var stringArray [][]string
	for _, mruItem := range window.Mru {
		stringArray = append(stringArray, []string{mruItem.DisplayName, mruItem.ProfilePath})
	}
	data, err := json.MarshalIndent(stringArray, "", "    ")
	if err != nil {
		log.Println("Error marshalling data: ", err)
		return
	}
	if err = os.WriteFile(window.MruFilename, data, 0666); err != nil {
		log.Println("Error writing profile file ", window.MruFilename, ":", err)
	}
}
