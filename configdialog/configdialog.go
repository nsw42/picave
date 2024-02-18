package configdialog

import (
	_ "embed"
	"nsw42/picave/players"
	"nsw42/picave/profile"
	"os"
	"path/filepath"
	"slices"

	"github.com/diamondburned/gotk4/pkg/gdk/v4"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
	"golang.org/x/exp/maps"
)

const (
	GridLeft  = 0
	GridRight = 1
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

func NewConfigDialog(parent *gtk.Window, profile *profile.Profile) *ConfigDialog {
	dialog := &ConfigDialog{}
	dialog.Dialog = gtk.NewDialogWithFlags("Configuration "+filepath.Base(profile.FilePath), parent, gtk.DialogModal)

	cssProvider := gtk.NewCSSProvider()
	cssProvider.LoadFromData(ConfigDialogCss)
	gtk.StyleContextAddProviderForDisplay(gdk.DisplayGetDefault(), cssProvider, gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

	dialog.Profile = profile
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
		dialog.Destroy()
	})

	return dialog
}

func (dialog *ConfigDialog) initExecutablesGrid() *gtk.Grid {
	grid := newGrid()
	y := 0
	executables := maps.Keys(dialog.Profile.Executables)
	slices.Sort(executables)
	for _, playerName := range executables {
		exePath := dialog.Profile.Executables[playerName]
		grid.Attach(gtk.NewLabel(playerName), GridLeft, y, 1, 1)
		grid.Attach(newTextEntry(exePath, nil), GridRight, y, 1, 1)
		y++
	}

	return grid
}

func (dialog *ConfigDialog) initFiletypesGrid() *gtk.Grid {
	grid := newGrid()
	y := 0
	filetypes := maps.Keys(dialog.Profile.FiletypePlayers)
	slices.Sort(filetypes)
	for _, filetypeSuffix := range filetypes {
		grid.Attach(gtk.NewLabel(filetypeSuffix), GridLeft, y, 1, 1)
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
		grid.Attach(dropdown, GridRight, y, 1, 1)
		y++
	}
	return grid
}

func (dialog *ConfigDialog) initGeneralGrid() *gtk.Grid {
	grid := newGrid()

	y := 0

	// Warm up music row
	grid.Attach(gtk.NewLabel("Warm up music"), GridLeft, y, 1, 1)
	dialog.WarmUpEntry = newTextEntry(dialog.Profile.WarmUpMusic.BasePath, validateDirectory)
	// TODO: ConnectChanged
	grid.Attach(dialog.WarmUpEntry, GridRight, y, 1, 1)
	y++

	// Video cache row
	grid.Attach(gtk.NewLabel("Video cache"), GridLeft, y, 1, 1)
	dialog.VideoCacheEntry = newTextEntry(dialog.Profile.VideoCacheDirectory, validateDirectory)
	// TODO: ConnectChanged
	grid.Attach(dialog.VideoCacheEntry, GridRight, y, 1, 1)
	y++

	// Default FTP row
	grid.Attach(gtk.NewLabel("Default FTP"), GridLeft, y, 1, 1)
	dialog.FtpSpinButton = newIntegerSpinner(0, 1000, dialog.Profile.DefaultFTPVal())
	grid.Attach(dialog.FtpSpinButton, GridRight, y, 1, 1)
	y++

	return grid
}
