package configdialog

import (
	"nsw42/picave/profile"

	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type OmxplayerParamsDialog struct {
	*gtk.Dialog
}

func NewOmxplayerParamsDialog(parent *gtk.Window, filetype string, options *profile.FiletypePlayerOptions) *OmxplayerParamsDialog {
	dialog := &OmxplayerParamsDialog{}
	dialog.Dialog = gtk.NewDialogWithFlags("omxplayer parameters for "+filetype, parent, gtk.DialogModal)

	grid := newGrid()
	y := 0
	topMarginSpinner := addRow(grid, &y, "Top margin", options.MarginTop)
	bottomMarginSpinner := addRow(grid, &y, "Bottom margin", options.MarginBottom)
	leftMarginSpinner := addRow(grid, &y, "Left margin", options.MarginLeft)
	rightMarginSpinner := addRow(grid, &y, "Right margin", options.MarginRight)

	dialog.ContentArea().Append(grid)

	dialog.AddButton("Cancel", int(gtk.ResponseCancel))
	dialog.AddButton("OK", int(gtk.ResponseOK))
	dialog.SetDefaultResponse(int(gtk.ResponseOK))

	dialog.ConnectResponse(func(responseId int) {
		if responseId == int(gtk.ResponseOK) {
			options.MarginTop = topMarginSpinner.ValueAsInt()
			options.MarginBottom = bottomMarginSpinner.ValueAsInt()
			options.MarginLeft = leftMarginSpinner.ValueAsInt()
			options.MarginRight = rightMarginSpinner.ValueAsInt()
		}
		dialog.Destroy()
	})

	return dialog
}

func addRow(grid *gtk.Grid, y *int, labelText string, initVal int) *gtk.SpinButton {
	grid.Attach(gtk.NewLabel(labelText), TwoColGridLeft, *y, 1, 1)
	spinner := newIntegerSpinner(-1024, 1024, initVal)
	grid.Attach(spinner, TwoColGridRight, *y, 1, 1)
	(*y)++
	return spinner
}
