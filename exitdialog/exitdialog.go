package exitdialog

import "github.com/diamondburned/gotk4/pkg/gtk/v4"

type ExitChoice int

const (
	ExitChoiceCancel ExitChoice = iota
	ExitChoiceChangeProfile
	ExitChoiceQuit
	ExitChoiceShutdown
)

type ExitDialog struct {
	*gtk.Dialog
}

func NewExitDialog(parent *gtk.Window) *ExitDialog {
	dialog := gtk.NewDialogWithFlags("Really quit?", parent, gtk.DialogModal)
	dialog.AddButton("Cancel", int(ExitChoiceCancel))
	dialog.AddButton("Change profile", int(ExitChoiceChangeProfile))
	dialog.AddButton("Quit", int(ExitChoiceQuit))
	dialog.AddButton("Shutdown", int(ExitChoiceShutdown))
	dialog.SetDefaultSize(150, 100)
	rtn := &ExitDialog{dialog}
	return rtn
}
