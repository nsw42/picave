package appwindow

import (
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type MainPanel struct {
	Parent   *AppWindow
	Contents *gtk.Box
}

const border = 300

func NewMainPanel(parent *AppWindow) *MainPanel {
	rtn := &MainPanel{Parent: parent}

	buttonBox := gtk.NewBox(gtk.OrientationVertical, 0)
	rtn.Contents = buttonBox

	buttonBox.SetMarginStart(border)
	buttonBox.SetMarginEnd(border)
	buttonBox.SetMarginTop(border)
	buttonBox.SetMarginBottom(border)

	configButton := gtk.NewButtonFromIconName("preferences-other-symbolic")
	configButton.SetHAlign(gtk.AlignEnd)
	configButton.SetVAlign(gtk.AlignStart)
	configButton.SetHExpand(false)
	configButton.SetVExpand(false)
	configButton.SetMarginBottom(100)
	buttonBox.Append(configButton)

	warmUpButton := gtk.NewButtonWithLabel("Warm up")
	warmUpButton.SetHExpand(true)
	warmUpButton.SetVExpand(true)
	warmUpButton.SetMarginBottom(200)
	buttonBox.Append(warmUpButton)
	warmUpButton.ConnectClicked(func() {
		parent.Stack.SetVisibleChildName(WarmUpPanelName)
		parent.WarmUpPanel.OnShown()
	})

	mainSessionButton := gtk.NewButtonWithLabel("Main session")
	mainSessionButton.SetHExpand(true)
	mainSessionButton.SetVExpand(true)
	buttonBox.Append(mainSessionButton)
	mainSessionButton.ConnectClicked(func() {
		parent.Stack.SetVisibleChildName(VideoIndexPanelName)
	})

	return rtn
}
