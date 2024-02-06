package appwindow

import (
	"fmt"
	"nsw42/picave/feed"
	"nsw42/picave/profile"

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
	EventController *gtk.EventControllerKey
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

	rtn.EventController = gtk.NewEventControllerKey()
	rtn.EventController.ConnectKeyPressed(rtn.OnKeyPress)
	rtn.GtkWindow.AddController(rtn.EventController)

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

func (window *AppWindow) OnBackKey() {
	window.StopPlaying()
	switch window.Stack.VisibleChildName() {
	case SessionPanelName:
		window.Stack.SetVisibleChildName(VideoIndexPanelName)
	case WarmUpPanelName, VideoIndexPanelName:
		window.Stack.SetVisibleChildName(MainPanelName)
	case MainPanelName:
		// TODO: quit dialog
	}
}

func (window *AppWindow) OnKeyPress(keyval uint, keycode uint, state gdk.ModifierType) bool {
	switch {
	case (keyval == 'c') && (state == 0): // OSMC 'index' button
		window.OnShowIndex()
		return true
	case (keyval == gdk.KEY_Escape) && (state == 0):
		window.OnShowHome()
		return true
	case keyval == 'X': // Simulate the OSMC 'back' button
		window.OnBackKey()
		return true
	}
	fmt.Println("Unhandled key press: keyval: ", keyval, "; keycode: ", keycode, "; modifier:", state)
	return false
}

func (window *AppWindow) OnShowHome() {
	window.StopPlaying()
	window.Stack.SetVisibleChildName(MainPanelName)
}

func (window *AppWindow) OnShowIndex() {
	window.StopPlaying()
	window.Stack.SetVisibleChildName(VideoIndexPanelName)
}

func (window *AppWindow) StopPlaying() {
	switch window.Stack.VisibleChildName() {
	case WarmUpPanelName:
		window.WarmUpPanel.Stop()
	case SessionPanelName:
		window.SessionPanel.Stop()
	}
}
