package configdialog

import (
	"nsw42/picave/profile"
	"nsw42/picave/widgets"

	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type OmxplayerParamsDialog struct {
	*gtk.Dialog
}

func NewOmxplayerParamsDialog(parent *gtk.Window, filetype string, margins *profile.Margins) *OmxplayerParamsDialog {
	dialog := &OmxplayerParamsDialog{}
	dialog.Dialog = gtk.NewDialogWithFlags("omxplayer parameters for "+filetype, parent, gtk.DialogModal)

	grid := newGrid()
	y := 0
	topMarginSpinner := addRow(grid, &y, "Top margin", margins.Top)
	bottomMarginSpinner := addRow(grid, &y, "Bottom margin", margins.Bottom)
	leftMarginSpinner := addRow(grid, &y, "Left margin", margins.Left)
	rightMarginSpinner := addRow(grid, &y, "Right margin", margins.Right)

	dialog.ContentArea().Append(grid)

	dialog.AddButton("Cancel", int(gtk.ResponseCancel))
	dialog.AddButton("OK", int(gtk.ResponseOK))
	dialog.SetDefaultResponse(int(gtk.ResponseOK))

	dialog.ConnectResponse(func(responseId int) {
		if responseId == int(gtk.ResponseOK) {
			margins.Top = topMarginSpinner.ValueAsInt()
			margins.Bottom = bottomMarginSpinner.ValueAsInt()
			margins.Left = leftMarginSpinner.ValueAsInt()
			margins.Right = rightMarginSpinner.ValueAsInt()
		}
		dialog.Destroy()
	})

	return dialog
}

func addRow(grid *gtk.Grid, y *int, labelText string, initVal int) *gtk.SpinButton {
	grid.Attach(gtk.NewLabel(labelText), TwoColGridLeft, *y, 1, 1)
	spinner := widgets.NewIntegerSpinner(-1024, 1024, initVal)
	grid.Attach(spinner, TwoColGridRight, *y, 1, 1)
	(*y)++
	return spinner
}
