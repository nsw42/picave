package profilechooser

import (
	"os"
	"strings"

	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

const (
	Left  = 0
	Right = 1
)

type AddDialog struct {
	*gtk.Dialog
	Parent           *ProfileChooserWindow
	DisplayNameEntry *gtk.Entry
	FilePathEntry    *gtk.Entry
}

func (window *ProfileChooserWindow) DoAddDialog() {
	dialog := &AddDialog{}
	dialog.Dialog = gtk.NewDialogWithFlags("Profile creator", &window.Window, gtk.DialogModal)
	dialog.Parent = window
	grid := gtk.NewGrid()
	grid.SetColumnSpacing(4)
	grid.SetRowSpacing(4)
	grid.SetMarginStart(8)
	grid.SetMarginEnd(8)
	grid.SetMarginTop(8)
	grid.SetMarginBottom(8)
	dialog.ContentArea().Append(grid)

	y := 0
	grid.Attach(gtk.NewLabel("Display name"), Left, y, 1, 1)
	dialog.DisplayNameEntry = gtk.NewEntry()
	grid.Attach(dialog.DisplayNameEntry, Right, y, 1, 1)
	y++

	grid.Attach(gtk.NewLabel("Config file"), Left, y, 1, 1)
	dialog.FilePathEntry = gtk.NewEntry()
	grid.Attach(dialog.FilePathEntry, Right, y, 1, 1)
	// TODO: Add a button to launch a FileChooserDialog
	y++

	dialog.AddButton("Cancel", int(gtk.ResponseCancel))
	dialog.AddButton("OK", int(gtk.ResponseOK))
	dialog.FilePathEntry.SetActivatesDefault(true)
	dialog.SetDefaultResponse(int(gtk.ResponseOK))

	dialog.ConnectResponse(dialog.OnAddResponse)

	dialog.Show()
}

func (dialog *AddDialog) OnAddResponse(responseId int) {
	if responseId == int(gtk.ResponseOK) {
		displayName := dialog.DisplayNameEntry.Text()
		filePath := dialog.FilePathEntry.Text()
		if strings.HasPrefix(filePath, "~/") {
			home, _ := os.UserHomeDir()
			filePath = home + "/" + filePath[2:]
		}
		dialog.Parent.Mru = append(dialog.Parent.Mru, MruEntry{displayName, filePath})
		dialog.Parent.AddListBoxEntry(displayName, true)
		dialog.Parent.SaveMru()
	}
	dialog.Destroy()
}
