package configdialog

import "github.com/diamondburned/gotk4/pkg/gtk/v4"

const (
	TwoColGridLeft  = 0
	TwoColGridRight = 1

	ThreeColGridLeft   = 0
	ThreeColGridMiddle = 1
	ThreeColGridRight  = 2
)

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
