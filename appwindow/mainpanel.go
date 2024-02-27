package appwindow

import (
	"log"
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
		dialog := configdialog.NewConfigDialog(&parent.Window,
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
	enabled := panel.ShouldEnableWarmUpButton()
	panel.WarmUpButton.SetSensitive(enabled)
}

func (panel *MainPanel) ShouldEnableWarmUpButton() bool {
	prf := panel.Parent.Profile
	if prf.WarmUpMusic == nil {
		log.Println("No warm up music folder configured")
		return false
	}

	if !prf.WarmUpMusic.Exists {
		log.Println("Warm up music directory configured, but it doesn't exist")
		return false
	}

	mp3Player := prf.FiletypePlayers[".mp3"]
	if mp3Player == nil {
		log.Println("No player enabled for .mp3 files")
		return false
	}

	exe := prf.Executables[mp3Player.Name]
	if exe == nil {
		log.Println("Could not find a definition for player ", mp3Player.Name)
		return false
	}

	if exe.ExePath() == "" {
		log.Println("Could not find the binary", exe.Name)
		return false
	}

	return true
}
