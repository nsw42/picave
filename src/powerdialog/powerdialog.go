package powerdialog

import (
	"nsw42/picave/feed"
	"nsw42/picave/profile"
	"nsw42/picave/widgets"
	"strconv"
	"strings"

	"github.com/diamondburned/gotk4/pkg/gdk/v4"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
	"golang.org/x/exp/slices"
)

type PowerDialog struct {
	*gtk.Dialog

	Profile *profile.Profile
	VideoId string

	FtpDefaultRadio    *gtk.CheckButton
	FtpAbsoluteRadio   *gtk.CheckButton
	FtpAbsoluteSpinner *gtk.SpinButton

	MaxDefaultRadio    *gtk.CheckButton
	MaxAbsoluteRadio   *gtk.CheckButton
	MaxAbsoluteSpinner *gtk.SpinButton
	MaxRelativeRadio   *gtk.CheckButton
	MaxRelativeSpinner *gtk.SpinButton

	CancelButton *gtk.Button
	OkButton     *gtk.Button

	Notebook *gtk.Notebook
}

func NewPowerDialog(parent *gtk.Window, prf *profile.Profile, videoId string, okCallback func()) *PowerDialog {
	dialog := &PowerDialog{}
	dialog.Dialog = gtk.NewDialogWithFlags("Power Customisation", parent, gtk.DialogModal)
	dialog.Profile = prf
	dialog.VideoId = videoId

	videoItem := feed.Index[slices.IndexFunc(feed.Index, func(item feed.VideoFeedItem) bool { return item.Id == videoId })]
	dialog.ContentArea().Append(gtk.NewLabel("Video: " + videoItem.Name))
	ftpBox := dialog.buildFtpPage()
	maxBox := dialog.buildMaxPage()

	dialog.Notebook = gtk.NewNotebook()
	dialog.Notebook.AppendPage(ftpBox, gtk.NewLabel("FTP"))
	dialog.Notebook.AppendPage(maxBox, gtk.NewLabel("Max"))
	dialog.ContentArea().Append(dialog.Notebook)

	dialog.CancelButton = dialog.AddButton("Cancel", int(gtk.ResponseCancel)).(*gtk.Button)
	dialog.OkButton = dialog.AddButton("OK", int(gtk.ResponseOK)).(*gtk.Button)
	dialog.SetDefaultResponse(int(gtk.ResponseOK))

	keyController := gtk.NewEventControllerKey()
	keyController.ConnectKeyPressed(dialog.OnKeyPress)
	dialog.Dialog.AddController(keyController)

	// Adding a keycontroller to the radio button seems to be necessary for us to be able to handle the
	// return key to trigger the default response - and there's no "activates-response" property on the checkbutton
	for _, radio := range []*gtk.CheckButton{dialog.FtpDefaultRadio, dialog.FtpAbsoluteRadio, dialog.MaxDefaultRadio, dialog.MaxAbsoluteRadio, dialog.MaxRelativeRadio} {
		keyController = gtk.NewEventControllerKey()
		keyController.ConnectKeyPressed(dialog.OnKeyPress)
		radio.AddController(keyController)
	}

	for _, spinner := range []*gtk.SpinButton{dialog.FtpAbsoluteSpinner, dialog.MaxAbsoluteSpinner, dialog.MaxRelativeSpinner} {
		keyController = gtk.NewEventControllerKey()
		keyController.ConnectKeyPressed(dialog.OnKeyPress)
		spinner.AddController(keyController)
		spinner.SetCanFocus(false)
	}

	dialog.ConnectResponse(func(responseId int) {
		if responseId == int(gtk.ResponseOK) {
			dialog.SaveValuesToProfile()
			prf.Save()
			okCallback()
		}
		dialog.Destroy()
	})

	return dialog
}

func (dialog *PowerDialog) SaveValuesToProfile() {
	prf := dialog.Profile

	switch {
	case dialog.FtpDefaultRadio.Active():
		prf.SetVideoFTPDefault(dialog.VideoId)
	case dialog.FtpAbsoluteRadio.Active():
		prf.SetVideoFTPVal(dialog.VideoId, dialog.FtpAbsoluteSpinner.ValueAsInt())
	}

	switch {
	case dialog.MaxDefaultRadio.Active():
		prf.SetVideoMaxDefault(dialog.VideoId)
	case dialog.MaxAbsoluteRadio.Active():
		prf.SetVideoMaxAbsolute(dialog.VideoId, dialog.MaxAbsoluteSpinner.ValueAsInt())
	case dialog.MaxRelativeRadio.Active():
		prf.SetVideoMaxRelative(dialog.VideoId, dialog.MaxRelativeSpinner.ValueAsInt())
	}
}

func (dialog *PowerDialog) OnKeyPress(keyval uint, keycode uint, state gdk.ModifierType) bool {
	// Focus handling for remote-control based navigation and configuration
	switch keyval {
	case gdk.KEY_Down, gdk.KEY_Up:
		return dialog.OnKeyPressUpDown(keyval)
	case gdk.KEY_Left:
		return dialog.OnKeyPressLeftRight(-1)
	case gdk.KEY_Right:
		return dialog.OnKeyPressLeftRight(1)
	case gdk.KEY_Return, gdk.KEY_KP_Enter:
		focussedRadio, _ := dialog.focussedRadioAndSpinButton()
		if !focussedRadio.Active() {
			// First press of OK to activate
			focussedRadio.Activate()
		} else {
			// Second press of OK to save
			dialog.OkButton.Activate()
		}
		return true
	default:
		return false
	}
}

func (dialog *PowerDialog) focussedRadioAndSpinButton() (*gtk.CheckButton, *gtk.SpinButton) {
	focussedControl := dialog.Focus()
	// Is the focus on the radiobutton part of the pair?
	radioButton, ok := focussedControl.(*gtk.CheckButton)
	if ok {
		switch {
		case radioButton.Eq(dialog.FtpDefaultRadio):
			return dialog.FtpDefaultRadio, nil
		case radioButton.Eq(dialog.FtpAbsoluteRadio):
			return dialog.FtpAbsoluteRadio, dialog.FtpAbsoluteSpinner
		case radioButton.Eq(dialog.MaxDefaultRadio):
			return dialog.MaxDefaultRadio, nil
		case radioButton.Eq(dialog.MaxAbsoluteRadio):
			return dialog.MaxAbsoluteRadio, dialog.MaxAbsoluteSpinner
		case radioButton.Eq(dialog.MaxRelativeRadio):
			return dialog.MaxRelativeRadio, dialog.MaxRelativeSpinner
		}
	}

	// Is the focus on the spinbutton part of the pair?
	text, ok := focussedControl.(*gtk.Text)
	if ok {
		var spinButton *gtk.SpinButton
		parent := text.Parent()
		spinButton, ok = parent.(*gtk.SpinButton)
		if ok {
			switch {
			case spinButton.Eq(dialog.FtpAbsoluteSpinner):
				return dialog.FtpAbsoluteRadio, dialog.FtpAbsoluteSpinner
			case spinButton.Eq(dialog.MaxAbsoluteSpinner):
				return dialog.MaxAbsoluteRadio, dialog.MaxAbsoluteSpinner
			case spinButton.Eq(dialog.MaxRelativeSpinner):
				return dialog.MaxRelativeRadio, dialog.MaxRelativeSpinner
			}
		}
	}
	return nil, nil
}

func (dialog *PowerDialog) OnKeyPressLeftRight(delta int) bool {
	focussedRadio, focussedSpinButton := dialog.focussedRadioAndSpinButton()
	if focussedRadio != nil {
		focussedRadio.Activate()
	}
	if focussedSpinButton != nil {
		focussedSpinButton.SetValue(focussedSpinButton.Value() + float64(delta))
		return true
	}
	return false
}

func (dialog *PowerDialog) OnKeyPressUpDown(keyval uint) bool {
	widgetToActivate := dialog.OnKeyPressUpDownGetWidgetToActivate(keyval)

	if widgetToActivate == nil {
		return false
	}

	radio, isRadioButton := widgetToActivate.Cast().(*gtk.CheckButton)
	if isRadioButton {
		// Don't activate it yet - might be passing through to get to OK
		// radio.Activate()
		dialog.SetFocus(radio)
	} else {
		// It's probably the OK button
		dialog.SetFocus(widgetToActivate)
	}
	return true
}

func (dialog *PowerDialog) OnKeyPressUpDownGetWidgetToActivate(keyval uint) *gtk.Widget {
	focussedControl := dialog.Focus()
	focussedNotebook, ok := focussedControl.(*gtk.Notebook)
	if ok && focussedNotebook.Eq(dialog.Notebook) {
		if keyval == gdk.KEY_Down {
			switch dialog.Notebook.CurrentPage() {
			case 0:
				return &dialog.FtpDefaultRadio.Widget
			case 1:
				return &dialog.MaxDefaultRadio.Widget
			}
		}
	}

	focussedRadio, focussedSpinButton := dialog.focussedRadioAndSpinButton()
	if focussedRadio == nil {
		return nil
	}

	var widgetDown, widgetUp *gtk.Widget

	switch {
	case focussedRadio.Eq(dialog.FtpDefaultRadio):
		widgetDown = &dialog.FtpAbsoluteRadio.Widget

	case focussedRadio.Eq(dialog.FtpAbsoluteRadio), focussedSpinButton != nil && focussedSpinButton.Eq(dialog.FtpAbsoluteSpinner):
		widgetUp = &dialog.FtpDefaultRadio.Widget
		widgetDown = &dialog.OkButton.Widget

	case focussedRadio.Eq(dialog.MaxDefaultRadio):
		widgetDown = &dialog.MaxAbsoluteRadio.Widget

	case focussedRadio.Eq(dialog.MaxAbsoluteRadio), focussedSpinButton != nil && focussedSpinButton.Eq(dialog.MaxAbsoluteSpinner):
		widgetUp = &dialog.MaxDefaultRadio.Widget
		widgetDown = &dialog.MaxRelativeRadio.Widget

	case focussedRadio.Eq(dialog.MaxRelativeRadio), focussedSpinButton != nil && focussedSpinButton.Eq(dialog.MaxRelativeSpinner):
		widgetUp = &dialog.MaxAbsoluteRadio.Widget
		widgetDown = &dialog.OkButton.Widget
	}

	if keyval == gdk.KEY_Down {
		return widgetDown
	} else {
		return widgetUp
	}
}

func (dialog *PowerDialog) buildDefaultPowerBox(defaultVal string) (*gtk.Box, *gtk.CheckButton) {
	box := gtk.NewBox(gtk.OrientationHorizontal, 6)
	radio := gtk.NewCheckButtonWithLabel("Default")
	radio.SetActive(true) // Might get undone later
	label := gtk.NewLabel("(" + defaultVal + ")")
	box.Append(radio)
	box.Append(label)
	return box, radio
}

func (dialog *PowerDialog) buildAbsolutePowerBox(defaultRadio *gtk.CheckButton, initVal int, active bool) (*gtk.Box, *gtk.CheckButton, *gtk.SpinButton) {
	box := gtk.NewBox(gtk.OrientationHorizontal, 6)
	radio := gtk.NewCheckButtonWithLabel("Power")
	radio.SetGroup(defaultRadio)
	spinner := widgets.NewIntegerSpinner(0, 1000, initVal)
	radio.SetActive(active)
	spinner.SetSensitive(active)

	radio.ConnectToggled(func() {
		spinner.SetSensitive(radio.Active())
	})

	box.Append(radio)
	box.Append(spinner)
	return box, radio, spinner
}

func (dialog *PowerDialog) buildRelativePowerBox(defaultRadio *gtk.CheckButton, initVal int, active bool) (*gtk.Box, *gtk.CheckButton, *gtk.SpinButton) {
	box := gtk.NewBox(gtk.OrientationHorizontal, 6)
	radio := gtk.NewCheckButtonWithLabel("%FTP")
	radio.SetGroup(defaultRadio)
	// relative_power_radio.connect("toggled", self.on_radio_button_toggled)

	spinner := widgets.NewIntegerSpinner(0, 500, initVal)
	// specified_power_spinbutton.set_activates_default(True)

	// Set the initial state for the radios
	radio.SetActive(active)
	spinner.SetSensitive(active)

	radio.ConnectToggled(func() {
		spinner.SetSensitive(radio.Active())
	})

	box.Append(radio)
	box.Append(spinner)
	return box, radio, spinner
}

func (dialog *PowerDialog) buildFtpPage() *gtk.Box {
	defaultFtpStr := dialog.Profile.DefaultFTP()
	// 1st radio button: o Default (123)
	defaultBox, defaultRadio := dialog.buildDefaultPowerBox(defaultFtpStr)
	// 2nd radio button: o Power [____]
	videoAbs := dialog.Profile.GetVideoFTPVal(dialog.VideoId, false)
	absActive := videoAbs > 0
	var initAbs int
	if videoAbs > 0 {
		initAbs = videoAbs
	} else {
		initAbs, _ = strconv.Atoi(defaultFtpStr)
	}
	absBox, absRadio, absSpinButton := dialog.buildAbsolutePowerBox(defaultRadio, initAbs, absActive)

	// Assemble the page of settings
	box := gtk.NewBox(gtk.OrientationVertical, 6)
	box.Append(defaultBox)
	box.Append(absBox)

	dialog.FtpDefaultRadio = defaultRadio
	dialog.FtpAbsoluteRadio = absRadio
	dialog.FtpAbsoluteSpinner = absSpinButton

	return box
}

func (dialog *PowerDialog) buildMaxPage() *gtk.Box {
	defaultFtpVal := dialog.Profile.DefaultFTPVal()
	defaultMax := dialog.Profile.DefaultMax()
	// Radio button group:
	// 1st radio button: o Default (123)
	defaultMaxVal := dialog.Profile.DefaultMaxVal()
	var defaultMaxStr string
	if defaultMaxVal == 0 {
		defaultMaxStr = "MAX"
	} else {
		defaultMaxStr = strconv.Itoa(defaultMaxVal)
	}
	defaultBox, defaultRadio := dialog.buildDefaultPowerBox(defaultMaxStr)
	// 2nd radio button: o Power [____]
	videoMax := dialog.Profile.GetVideoMax(dialog.VideoId, false)
	absActive := (videoMax != "") && (!strings.HasSuffix(videoMax, "%"))
	var initAbs int
	if absActive {
		initAbs = dialog.Profile.GetVideoMaxVal(dialog.VideoId, false)
	} else if defaultMaxVal > 0 {
		initAbs = defaultMaxVal
	} else {
		initAbs = defaultFtpVal * 2
	}
	absBox, absRadio, absSpinButton := dialog.buildAbsolutePowerBox(defaultRadio, initAbs, absActive)
	// 3rd radio button: o %FTP [____]
	relActive := (videoMax != "") && (strings.HasSuffix(videoMax, "%"))
	var initRel int
	if relActive {
		initRel = intFromPercentString(videoMax)
	} else {
		if strings.HasSuffix(defaultMax, "%") {
			initRel = intFromPercentString(defaultMax)
		} else {
			initRel = 200
		}
	}
	relBox, relRadio, relSpinButton := dialog.buildRelativePowerBox(defaultRadio, initRel, relActive)

	box := gtk.NewBox(gtk.OrientationVertical, 6)
	box.Append(defaultBox)
	box.Append(absBox)
	box.Append(relBox)

	dialog.MaxDefaultRadio = defaultRadio
	dialog.MaxAbsoluteRadio = absRadio
	dialog.MaxAbsoluteSpinner = absSpinButton
	dialog.MaxRelativeRadio = relRadio
	dialog.MaxRelativeSpinner = relSpinButton

	return box
}

func intFromPercentString(pct string) int {
	prefix, _ := strings.CutSuffix(pct, "%")
	val, _ := strconv.Atoi(prefix)
	return val
}
