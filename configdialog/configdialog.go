package configdialog

import (
	_ "embed"
	"nsw42/picave/musicdir"
	"nsw42/picave/players"
	"nsw42/picave/profile"
	"os"
	"path/filepath"
	"slices"
	"strings"

	// coreglib "github.com/diamondburned/gotk4/pkg/core/glib"
	"github.com/diamondburned/gotk4/pkg/gdk/v4"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
	"golang.org/x/exp/maps"
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
	FiletypeControls map[string]*FiletypeControl // key is the filetype (".mp4", etc)
}

type FiletypeControl struct {
	DropDown *gtk.DropDown
	Entry    *gtk.Entry
	Margins  profile.Margins
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

func validateOptionalDirectory(dirname string) bool {
	if dirname == "" {
		return true
	}
	return validateDirectory(dirname)
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

func NewConfigDialog(parent *gtk.Window, prf *profile.Profile, okCallback func()) *ConfigDialog {
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
			if dialog.WarmUpEntry.Text() == "" {
				prf.WarmUpMusic = nil
			} else {
				prf.WarmUpMusic = musicdir.NewMusicDirectory(dialog.WarmUpEntry.Text())
			}
			prf.VideoCacheDirectory = dialog.VideoCacheEntry.Text()
			prf.SetDefaultFTPVal(int(dialog.FtpSpinButton.Value()))

			// Executables tab:
			for exeName, entry := range dialog.ExecutableEntryBoxes {
				prf.Executables[exeName] = profile.NewExecutable(exeName, entry.Text())
			}

			// Filetypes tab:
			for filetypeSuffix, controls := range dialog.FiletypeControls {
				player := controls.DropDown.SelectedItem().Cast().(*gtk.StringObject).String()
				dialog.Profile.FiletypePlayers[filetypeSuffix] = &profile.FiletypePlayerOptions{
					Name:    player,
					Options: strings.Split(controls.Entry.Text(), " "),
					Margins: controls.Margins,
				}
			}

			// And save it
			prf.Save()

			// Ensure that the 'warm up button' on the main panel is enabled/disabled appropriately,
			// and that the 'downloaded' icons in the session panel are updated.
			okCallback()
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
		entry := newTextEntry(exePath.ConfiguredPath, validateExecutable)
		dialog.ExecutableEntryBoxes[exeName] = entry
		grid.Attach(entry, TwoColGridRight, y, 1, 1)
		y++
	}

	return grid
}

func (dialog *ConfigDialog) initFiletypesGrid() *gtk.Grid {
	grid := newGrid()
	grid.SetColumnHomogeneous(false)
	y := 0
	grid.Attach(gtk.NewLabel("Filetype"), ThreeColGridLeft, y, 1, 1)
	grid.Attach(gtk.NewLabel("Application"), ThreeColGridMiddle, y, 1, 1)
	grid.Attach(gtk.NewLabel("Options"), ThreeColGridRight, y, 1, 1)
	y++
	filetypes := maps.Keys(dialog.Profile.FiletypePlayers)
	slices.Sort(filetypes)
	dialog.FiletypeControls = make(map[string]*FiletypeControl, len(filetypes))
	for _, filetypeSuffix := range filetypes {
		// left: label
		grid.Attach(gtk.NewLabel(filetypeSuffix), ThreeColGridLeft, y, 1, 1)
		// middle: dropdown
		var playerNames []string
		if filetypeSuffix == ".mp3" {
			playerNames = maps.Keys[map[string]players.MusicPlayerCreator](players.MusicPlayerLookup)
		} else {
			playerNames = maps.Keys[map[string]players.VideoPlayerCreator](players.VideoPlayerLookup)
		}
		filetypePlayer := dialog.Profile.FiletypePlayers[filetypeSuffix]
		dropdown := gtk.NewDropDownFromStrings(playerNames)
		dropdown.SetSelected(uint(slices.Index(playerNames, filetypePlayer.Name)))
		grid.Attach(dropdown, ThreeColGridMiddle, y, 1, 1)
		// right: options and parameters
		optsAndParamsBox := gtk.NewBox(gtk.OrientationHorizontal, 6)
		optsEntry := gtk.NewEntry()
		optsEntry.SetText(strings.Join(filetypePlayer.Options, " "))
		optsEntry.SetHExpand(true)
		optsAndParamsBox.Append(optsEntry)
		paramsButton := gtk.NewButtonWithLabel("Parameters")
		paramsButton.ConnectClicked(func() {
			dialog.OnFiletypePlayerParamsButtonClicked(filetypeSuffix)
		})
		if filetypePlayer.Name != "omxplayer" {
			paramsButton.Hide()
		}
		dropdown.Connect("notify::selected-item", func() {
			if dropdown.SelectedItem().Cast().(*gtk.StringObject).String() == "omxplayer" {
				paramsButton.Show()
			} else {
				paramsButton.Hide()
			}
		})
		optsAndParamsBox.Append(paramsButton)
		grid.Attach(optsAndParamsBox, ThreeColGridRight, y, 1, 1)

		dialog.FiletypeControls[filetypeSuffix] = &FiletypeControl{dropdown, optsEntry, filetypePlayer.Margins}
		y++
	}
	return grid
}

func (dialog *ConfigDialog) OnFiletypePlayerParamsButtonClicked(filetypeSuffix string) {
	paramsDialog := NewOmxplayerParamsDialog(&dialog.Window, filetypeSuffix, &dialog.FiletypeControls[filetypeSuffix].Margins)
	paramsDialog.Show()
}

func (dialog *ConfigDialog) initGeneralGrid() *gtk.Grid {
	grid := newGrid()

	y := 0

	// Warm up music row
	grid.Attach(gtk.NewLabel("Warm up music"), TwoColGridLeft, y, 1, 1)
	var basePath string
	if dialog.Profile.WarmUpMusic != nil {
		basePath = dialog.Profile.WarmUpMusic.BasePath
	}
	dialog.WarmUpEntry = newTextEntry(basePath, validateOptionalDirectory)
	grid.Attach(dialog.WarmUpEntry, TwoColGridRight, y, 1, 1)
	y++

	// Video cache row
	grid.Attach(gtk.NewLabel("Video cache"), TwoColGridLeft, y, 1, 1)
	dialog.VideoCacheEntry = newTextEntry(dialog.Profile.VideoCacheDirectory, validateDirectory)
	grid.Attach(dialog.VideoCacheEntry, TwoColGridRight, y, 1, 1)
	y++

	// Default FTP row
	grid.Attach(gtk.NewLabel("Default FTP"), TwoColGridLeft, y, 1, 1)
	dialog.FtpSpinButton = newIntegerSpinner(0, 1000, dialog.Profile.DefaultFTPVal())
	grid.Attach(dialog.FtpSpinButton, TwoColGridRight, y, 1, 1)
	y++

	return grid
}
