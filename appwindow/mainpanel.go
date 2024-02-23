package appwindow

import (
	"nsw42/picave/configdialog"

	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type MainPanel struct {
	Parent            *AppWindow
	Contents          *gtk.Box
	ConfigButton      *gtk.Button
	WarmUpButton      *gtk.Button
	MainSessionButton *gtk.Button
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
	configButton.ConnectClicked(func() {
		dialog := configdialog.NewConfigDialog(&parent.GtkWindow.Window,
			parent.Profile,
			func() {
				rtn.SetWarmUpButtonSensitive()
				parent.VideoCacheDirectoryUpdated()
			})
		dialog.Show()
	})
	rtn.ConfigButton = configButton

	warmUpButton := gtk.NewButtonWithLabel("Warm up")
	warmUpButton.SetHExpand(true)
	warmUpButton.SetVExpand(true)
	warmUpButton.SetMarginBottom(200)
	buttonBox.Append(warmUpButton)
	warmUpButton.ConnectClicked(func() {
		parent.Stack.SetVisibleChildName(WarmUpPanelName)
		parent.WarmUpPanel.OnShown()
	})
	rtn.WarmUpButton = warmUpButton
	rtn.SetWarmUpButtonSensitive()

	mainSessionButton := gtk.NewButtonWithLabel("Main session")
	mainSessionButton.SetHExpand(true)
	mainSessionButton.SetVExpand(true)
	buttonBox.Append(mainSessionButton)
	mainSessionButton.ConnectClicked(func() {
		parent.Stack.SetVisibleChildName(VideoIndexPanelName)
	})
	rtn.MainSessionButton = mainSessionButton

	return rtn
}

func (panel *MainPanel) SetWarmUpButtonSensitive() {
	enabled := false
	prf := panel.Parent.Profile
	if prf.WarmUpMusic != nil {
		mp3Player := prf.FiletypePlayers["mp3"]
		if mp3Player != nil {
			exe := prf.Executables[mp3Player.Name]
			if exe != nil {
				if exe.ExePath() != "" {
					enabled = true
				}
			}
		}
	}
	panel.WarmUpButton.SetSensitive(enabled)
}
