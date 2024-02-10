package appwindow

import (
	"fmt"
	"nsw42/picave/exitdialog"
	"nsw42/picave/feed"
	"nsw42/picave/profile"
	"os/exec"

	"github.com/diamondburned/gotk4/pkg/gdk/v4"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type AppWindow struct {
	Profile         *profile.Profile
	GtkWindow       *gtk.ApplicationWindow
	Stack           *gtk.Stack
	MainPanel       *MainPanel
	WarmUpPanel     *WarmUpPanel
	VideoIndexPanel *VideoIndexPanel
	SessionPanel    *SessionPanel
	FeedCache       *feed.FeedCache
	KeyController   *gtk.EventControllerKey
}

func NewAppWindow(app *gtk.Application,
	profile *profile.Profile,
	fullScreen bool,
) *AppWindow {
	rtn := &AppWindow{Profile: profile}
	rtn.GtkWindow = gtk.NewApplicationWindow(app)
	rtn.GtkWindow.SetTitle("PiCave")

	rtn.FeedCache = feed.NewFeedCache(profile)

	rtn.Stack = gtk.NewStack()
	rtn.GtkWindow.SetChild(rtn.Stack)
	rtn.Stack.SetTransitionType(gtk.StackTransitionTypeSlideLeftRight)
	rtn.Stack.SetTransitionDuration(1000)

	rtn.KeyController = gtk.NewEventControllerKey()
	rtn.KeyController.ConnectKeyPressed(rtn.OnKeyPress)
	rtn.GtkWindow.AddController(rtn.KeyController)

	if fullScreen {
		rtn.GtkWindow.Fullscreen()
	} else {
		display := gdk.DisplayGetDefault()
		monitors := display.Monitors()
		// var primary *gdk.Monitor
		primary := monitors.Item(0).Cast().(*gdk.Monitor)
		geometry := primary.Geometry()
		// TODO: Is there a better option? GTK4 removed monitor.GetWorkArea,
		// which would leave space for macOS menu bar.
		rtn.GtkWindow.SetSizeRequest(geometry.Width(), geometry.Height())
	}

	rtn.MainPanel = NewMainPanel(rtn)
	rtn.WarmUpPanel = NewWarmUpPanel(rtn)
	rtn.VideoIndexPanel = NewVideoIndexPanel(rtn)
	rtn.SessionPanel = NewSessionPanel(rtn)

	rtn.Stack.AddNamed(rtn.MainPanel.Contents, MainPanelName)
	rtn.Stack.AddNamed(rtn.WarmUpPanel.Contents, WarmUpPanelName)
	rtn.Stack.AddNamed(rtn.VideoIndexPanel.Contents, VideoIndexPanelName)
	rtn.Stack.AddNamed(rtn.SessionPanel.Contents, SessionPanelName)

	rtn.Stack.SetVisibleChildName(MainPanelName)

	return rtn
}

func (window *AppWindow) DoQuitDialog() {
	dialog := exitdialog.NewExitDialog(&window.GtkWindow.Window)
	dialog.ConnectResponse(func(responseId int) {
		switch exitdialog.ExitChoice(responseId) {
		case exitdialog.ExitChoiceCancel:
			// Nothing needed
		case exitdialog.ExitChoiceChangeProfile:
			// Not yet supported
		case exitdialog.ExitChoiceQuit:
			window.OnQuit()
		case exitdialog.ExitChoiceShutdown:
			window.OnShutdown()
		}
		dialog.Destroy()
	})
	dialog.Show()
}

func (window *AppWindow) OnBackKey() {
	window.StopPlaying()
	switch window.Stack.VisibleChildName() {
	case SessionPanelName:
		window.Stack.SetVisibleChildName(VideoIndexPanelName)
	case WarmUpPanelName, VideoIndexPanelName:
		window.Stack.SetVisibleChildName(MainPanelName)
	case MainPanelName:
		window.DoQuitDialog()
	}
}

func (window *AppWindow) OnKeyPress(keyval uint, keycode uint, state gdk.ModifierType) bool {
	switch {
	default:
		fmt.Println("Unhandled key press: keyval: ", keyval, "; keycode: ", keycode, "; modifier:", state)
		return false
	case (keyval == 'c') && (state == 0): // OSMC 'index' button
		window.OnShowIndex()
	case (keyval == gdk.KEY_Escape) && (state == 0):
		window.OnShowHome()
	case (keyval == gdk.KEY_Escape) && (state.Has(gdk.ShiftMask)):
		window.DoQuitDialog()
	case keyval == 'X': // Simulate the OSMC 'back' button
		window.OnBackKey()
	case keyval == 'p' || keyval == 'P': // Simulate the OSMC play/pause button
		window.OnPlayPause()
	}
	return true
}

func (window *AppWindow) OnPlayPause() {
	switch window.Stack.VisibleChildName() {
	case WarmUpPanelName:
		window.WarmUpPanel.OnPlayPause()
	case SessionPanelName:
		window.SessionPanel.OnPlayPause()
	}
}

func (window *AppWindow) OnQuit() {
	window.StopPlaying()
	window.GtkWindow.Application().Quit()
}

func (window *AppWindow) OnShowHome() {
	window.StopPlaying()
	window.Stack.SetVisibleChildName(MainPanelName)
}

func (window *AppWindow) OnShowIndex() {
	window.StopPlaying()
	window.Stack.SetVisibleChildName(VideoIndexPanelName)
}

func (window *AppWindow) OnShutdown() {
	window.OnQuit()
	cmd := exec.Command("sudo", "shutdown", "-h", "+1")
	cmd.Run()
}

func (window *AppWindow) StopPlaying() {
	switch window.Stack.VisibleChildName() {
	case WarmUpPanelName:
		window.WarmUpPanel.Stop()
	case SessionPanelName:
		window.SessionPanel.Stop()
	}
}
