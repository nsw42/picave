package configdialog

import (
	_ "embed"
	"nsw42/picave/musicdir"
	"nsw42/picave/players"
	"nsw42/picave/profile"
	"os"
	"path/filepath"
	"slices"

	// coreglib "github.com/diamondburned/gotk4/pkg/core/glib"
	"github.com/diamondburned/gotk4/pkg/gdk/v4"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
	"golang.org/x/exp/maps"
)

const (
	TwoColGridLeft  = 0
	TwoColGridRight = 1

	ThreeColGridLeft   = 0
	ThreeColGridMiddle = 1
	ThreeColGridRight  = 2
)

//go:embed "configdialog.css"
var ConfigDialogCss string

type ConfigDialog struct {
	*gtk.Dialog

	Profile *profile.Profile
	Stack   *gtk.Stack

	// Fields related to the General panel
	WarmUpEntry     *gtk.Entry
	VideoCacheEntry *gtk.Entry
	FtpSpinButton   *gtk.SpinButton

	// Fields related to the Executables panel
	ExecutableEntryBoxes map[string]*gtk.Entry // key is the executable name ("mpv", etc)

	// Fields related to the Filetypes panel
	FiletypeDropDowns map[string]*gtk.DropDown // key is the filetype (".mp4", etc)
}

func newGrid() *gtk.Grid {
	grid := gtk.NewGrid()
	grid.SetColumnSpacing(4)
	grid.SetRowSpacing(4)
	grid.SetMarginStart(8)
	grid.SetMarginEnd(8)
	grid.SetMarginTop(8)
	grid.SetMarginBottom(8)
	grid.SetHExpand(true)
	grid.SetVExpand(false)
	return grid
}

func newIntegerSpinner(lower, upper, value int) *gtk.SpinButton {
	adjustment := gtk.NewAdjustment(float64(value), float64(lower), float64(upper), 1.0, 5.0, 0.0)
	return gtk.NewSpinButton(adjustment, 1.0, 0)
}

func newTextEntry(initVal string, validator func(string) bool) *gtk.Entry {
	// Validators must return true if the given string is valid
	entry := gtk.NewEntry()
	entry.SetText(initVal)
	entry.SetHExpand(true)
	if validator != nil {
		entry.ConnectChanged(func() {
			newValue := entry.Text()
			ok := validator(newValue)
			if ok {
				entry.RemoveCSSClass("error")
			} else {
				entry.AddCSSClass("error")
			}
		})
	}
	return entry
}

func validateDirectory(dirname string) bool {
	if dirname == "" {
		return false
	}
	info, err := os.Stat(dirname)
	if err != nil {
		return false
	}
	return info.IsDir()
}

func validateExecutable(exename string) bool {
	if exename == "" {
		// Empty means "this player is disabled/not available"
		return true
	}
	info, err := os.Stat(exename)
	if err != nil || info.IsDir() {
		// If an error, then we probably don't have permission to access it, or it doesn't exist
		return false
	}
	if (info.Mode().Perm() & 1) != 0 {
		// executable
		return true
	}
	return false
}

func NewConfigDialog(parent *gtk.Window, prf *profile.Profile) *ConfigDialog {
	dialog := &ConfigDialog{}
	dialog.Dialog = gtk.NewDialogWithFlags("Configuration "+filepath.Base(prf.FilePath), parent, gtk.DialogModal)

	cssProvider := gtk.NewCSSProvider()
	cssProvider.LoadFromData(ConfigDialogCss)
	gtk.StyleContextAddProviderForDisplay(gdk.DisplayGetDefault(), cssProvider, gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

	dialog.Profile = prf
	dialog.Stack = gtk.NewStack()

	dialog.Stack.AddTitled(dialog.initGeneralGrid(), "general", "General")
	dialog.Stack.AddTitled(dialog.initExecutablesGrid(), "executables", "Executables")
	dialog.Stack.AddTitled(dialog.initFiletypesGrid(), "filetypes", "Filetypes")

	switcher := gtk.NewStackSwitcher()
	switcher.SetStack(dialog.Stack)

	vbox := gtk.NewBox(gtk.OrientationVertical, 6)
	vbox.Append(switcher)
	vbox.Append(dialog.Stack)

	dialog.ContentArea().Append(vbox)

	dialog.AddButton("Cancel", int(gtk.ResponseCancel))
	dialog.AddButton("OK", int(gtk.ResponseOK))
	dialog.SetDefaultResponse(int(gtk.ResponseOK))

	dialog.ConnectResponse(func(responseId int) {
		if responseId == int(gtk.ResponseOK) {
			// Update the profile
			// General tab:
			prf.WarmUpMusic = musicdir.NewMusicDirectory(dialog.WarmUpEntry.Text())
			prf.VideoCacheDirectory = dialog.VideoCacheEntry.Text()
			prf.SetDefaultFTPVal(int(dialog.FtpSpinButton.Value()))

			// Executables tab:
			for exeName, entry := range dialog.ExecutableEntryBoxes {
				prf.Executables[exeName] = entry.Text()
			}

			// Filetypes tab:
			for filetypeSuffix, dropdown := range dialog.FiletypeDropDowns {
				player := dropdown.SelectedItem().Cast().(*gtk.StringObject).String()
				dialog.Profile.FiletypePlayers[filetypeSuffix] = &profile.FiletypePlayerOptions{
					Name:    player,
					Options: []string{},
				}
			}

			// And save it
			prf.Save()
		}
		dialog.Destroy()
	})

	return dialog
}

func (dialog *ConfigDialog) initExecutablesGrid() *gtk.Grid {
	grid := newGrid()
	y := 0
	grid.Attach(gtk.NewLabel("Executable"), TwoColGridLeft, y, 1, 1)
	grid.Attach(gtk.NewLabel("Path"), TwoColGridRight, y, 1, 1)
	y++
	executableNames := maps.Keys(dialog.Profile.Executables)
	slices.Sort(executableNames)
	dialog.ExecutableEntryBoxes = make(map[string]*gtk.Entry, len(executableNames))
	for _, exeName := range executableNames {
		exePath := dialog.Profile.Executables[exeName]
		grid.Attach(gtk.NewLabel(exeName), TwoColGridLeft, y, 1, 1)
		entry := newTextEntry(exePath, validateExecutable)
		dialog.ExecutableEntryBoxes[exeName] = entry
		grid.Attach(entry, TwoColGridRight, y, 1, 1)
		y++
	}

	return grid
}

func (dialog *ConfigDialog) initFiletypesGrid() *gtk.Grid {
	grid := newGrid()
	y := 0
	grid.Attach(gtk.NewLabel("Filetype"), ThreeColGridLeft, y, 1, 1)
	grid.Attach(gtk.NewLabel("Application"), ThreeColGridMiddle, y, 1, 1)
	y++
	filetypes := maps.Keys(dialog.Profile.FiletypePlayers)
	slices.Sort(filetypes)
	dialog.FiletypeDropDowns = make(map[string]*gtk.DropDown, len(filetypes))
	for _, filetypeSuffix := range filetypes {
		grid.Attach(gtk.NewLabel(filetypeSuffix), ThreeColGridLeft, y, 1, 1)
		playerNames := []string{}
		if filetypeSuffix == ".mp3" {
			for playerName := range players.MusicPlayerLookup {
				playerNames = append(playerNames, playerName)
			}
		} else {
			for playerName := range players.VideoPlayerLookup {
				playerNames = append(playerNames, playerName)
			}
		}
		dropdown := gtk.NewDropDownFromStrings(playerNames)
		dropdown.SetHExpand(true)
		dropdown.SetSelected(uint(slices.Index(playerNames, dialog.Profile.FiletypePlayers[filetypeSuffix].Name)))
		dialog.FiletypeDropDowns[filetypeSuffix] = dropdown
		grid.Attach(dropdown, ThreeColGridMiddle, y, 1, 1)
		y++
	}
	return grid
}

func (dialog *ConfigDialog) initGeneralGrid() *gtk.Grid {
	grid := newGrid()

	y := 0

	// Warm up music row
	grid.Attach(gtk.NewLabel("Warm up music"), TwoColGridLeft, y, 1, 1)
	dialog.WarmUpEntry = newTextEntry(dialog.Profile.WarmUpMusic.BasePath, validateDirectory)
	// TODO: ConnectChanged
	grid.Attach(dialog.WarmUpEntry, TwoColGridRight, y, 1, 1)
	y++

	// Video cache row
	grid.Attach(gtk.NewLabel("Video cache"), TwoColGridLeft, y, 1, 1)
	dialog.VideoCacheEntry = newTextEntry(dialog.Profile.VideoCacheDirectory, validateDirectory)
	// TODO: ConnectChanged
	grid.Attach(dialog.VideoCacheEntry, TwoColGridRight, y, 1, 1)
	y++

	// Default FTP row
	grid.Attach(gtk.NewLabel("Default FTP"), TwoColGridLeft, y, 1, 1)
	dialog.FtpSpinButton = newIntegerSpinner(0, 1000, dialog.Profile.DefaultFTPVal())
	grid.Attach(dialog.FtpSpinButton, TwoColGridRight, y, 1, 1)
	y++

	return grid
}
