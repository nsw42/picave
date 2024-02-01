package appwindow

import (
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type WarmUpPanel struct {
	Parent        *AppWindow
	Contents      *gtk.Grid
	ArtistLabel   *gtk.Label
	TitleLabel    *gtk.Label
	TimeLabel     *gtk.Label
	DurationLabel *gtk.Label
	Pad           *gtk.Fixed
	NextButton    *gtk.Button
	BackButton    *gtk.Button
}

func expandingLabel(contents string) *gtk.Label {
	label := gtk.NewLabel(contents)
	label.SetHExpand(true)
	label.SetVExpand(true)
	return label
}

func NewWarmUpPanel(parent *AppWindow) *WarmUpPanel {
	rtn := &WarmUpPanel{Parent: parent}

	rtn.ArtistLabel = expandingLabel("<artist>")
	rtn.TitleLabel = expandingLabel("<title>")
	rtn.TimeLabel = expandingLabel("<time>")
	rtn.TimeLabel.SetHAlign(gtk.AlignEnd)
	rtn.DurationLabel = expandingLabel("/ <duration>")
	rtn.DurationLabel.SetHAlign(gtk.AlignStart)

	// TODO: Fonts

	timeHBox := gtk.NewBox(gtk.OrientationHorizontal, 0)
	timeHBox.Append(rtn.TimeLabel)
	timeHBox.Append(rtn.DurationLabel)

	rtn.Pad = gtk.NewFixed()

	rtn.NextButton = gtk.NewButtonWithLabel("Next track")
	rtn.NextButton.SetVExpand(false)
	rtn.BackButton = gtk.NewButtonWithLabel("Back")
	rtn.BackButton.SetHExpand(true)
	rtn.BackButton.SetSizeRequest(0, 80) // width is set by grid
	rtn.BackButton.ConnectClicked(func() { parent.Stack.SetVisibleChildName(MainPanelName) })

	//       0         1             2
	//  0            artist
	//  1   pad      title          Next
	//  2        time/duration
	//  3            Back

	grid := gtk.NewGrid()
	// row 0: artist
	grid.Attach(rtn.ArtistLabel, 1, 0, 1, 1)
	// row 1: pad, title, next
	grid.Attach(rtn.Pad, 0, 1, 1, 1)
	grid.Attach(rtn.TitleLabel, 1, 1, 1, 1)
	grid.Attach(rtn.NextButton, 2, 1, 1, 1)
	// row 2: time/duration (in the hbox)
	grid.Attach(timeHBox, 1, 2, 1, 1)
	// roe 3: back
	grid.Attach(rtn.BackButton, 1, 3, 1, 1)
	grid.SetMarginTop(200)
	grid.SetMarginBottom(200)
	grid.SetMarginStart(200)
	grid.SetMarginEnd(200)
	rtn.Contents = grid

	grid.ConnectRealize(rtn.OnRealized)

	return rtn
}

func (panel *WarmUpPanel) OnRealized() {
	panel.NextButton.GrabFocus()
}

func (panel *WarmUpPanel) OnShown() {
	_, naturalSize := panel.NextButton.PreferredSize()
	naturalSize.Width()
	panel.Pad.SetSizeRequest(naturalSize.Width(), 32)

}
