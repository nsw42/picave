package appwindow

import (
	"nsw42/picave/exitdialog"
	"nsw42/picave/feed"
	"nsw42/picave/osmc"
	"nsw42/picave/profile"
	"os/exec"

	"github.com/diamondburned/gotk4/pkg/gdk/v4"
	"github.com/diamondburned/gotk4/pkg/glib/v2"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type AppWindow struct {
	*gtk.ApplicationWindow
	Profile           *profile.Profile
	Stack             *gtk.Stack
	MainPanel         *MainPanel
	WarmUpPanel       *WarmUpPanel
	VideoIndexPanel   *VideoIndexPanel
	SessionPanel      *SessionPanel
	FeedCache         *feed.FeedCache
	KeyController     *gtk.EventControllerKey
	Osmc              osmc.Osmc
	RunProfileChooser func()
}

func NewAppWindow(app *gtk.Application,
	prf *profile.Profile,
	fullScreen bool,
	developerMode bool,
	hideMousePointer bool,
	runProfileChooserCallback func(),
) *AppWindow {
	rtn := &AppWindow{Profile: prf}
	rtn.ApplicationWindow = gtk.NewApplicationWindow(app)
	rtn.SetTitle("PiCave")

	rtn.FeedCache = feed.NewFeedCache(prf)

	rtn.Stack = gtk.NewStack()
	rtn.SetChild(rtn.Stack)
	rtn.Stack.SetTransitionType(gtk.StackTransitionTypeSlideLeftRight)
	rtn.Stack.SetTransitionDuration(1000)

	rtn.KeyController = gtk.NewEventControllerKey()
	rtn.KeyController.ConnectKeyPressed(rtn.OnKeyPress)
	rtn.AddController(rtn.KeyController)

	if fullScreen {
		rtn.Fullscreen()
	} else {
		display := gdk.DisplayGetDefault()
		monitors := display.Monitors()
		// var primary *gdk.Monitor
		primary := monitors.Item(0).Cast().(*gdk.Monitor)
		geometry := primary.Geometry()
		// TODO: Is there a better option? GTK4 removed monitor.GetWorkArea,
		// which would leave space for macOS menu bar.
		rtn.SetSizeRequest(geometry.Width(), geometry.Height())
	}

	rtn.MainPanel = NewMainPanel(rtn)
	rtn.WarmUpPanel = NewWarmUpPanel(rtn)
	rtn.VideoIndexPanel = NewVideoIndexPanel(rtn, developerMode)
	rtn.SessionPanel = NewSessionPanel(rtn)

	rtn.Stack.AddNamed(rtn.MainPanel.Contents, MainPanelName)
	rtn.Stack.AddNamed(rtn.WarmUpPanel.Contents, WarmUpPanelName)
	rtn.Stack.AddNamed(rtn.VideoIndexPanel.Contents, VideoIndexPanelName)
	rtn.Stack.AddNamed(rtn.SessionPanel.Contents, SessionPanelName)

	rtn.Stack.SetVisibleChildName(MainPanelName)

	rtn.Osmc = osmc.NewOsmcRemoteControlReader("")
	glib.TimeoutAdd(50, rtn.PollOsmc)

	pollForMedia := false
	if !prf.WarmUpMusic.Exists {
		pollForMedia = true
	}
	if !rtn.FeedCache.BaseDirExists {
		pollForMedia = true
	}
	if pollForMedia {
		glib.TimeoutAdd(1000, rtn.PollForMedia)
	}

	rtn.RunProfileChooser = runProfileChooserCallback

	if hideMousePointer {
		rtn.ConnectRealize(func() {
			rtn.Window.SetCursorFromName("none")
		})
	}

	rtn.ConnectCloseRequest(func() bool {
		if rtn.FeedCache != nil {
			rtn.FeedCache.StopUpdating()
		}
		return false // Allow other handlers to be invoked
	})

	return rtn
}

func (window *AppWindow) DoQuitDialog() {
	dialog := exitdialog.NewExitDialog(&window.Window)
	dialog.ConnectResponse(func(responseId int) {
		switch exitdialog.ExitChoice(responseId) {
		case exitdialog.ExitChoiceCancel:
			// Nothing needed
		case exitdialog.ExitChoiceChangeProfile:
			window.Close()
			window.RunProfileChooser()
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
		// log.Println("Unhandled key press: keyval: ", keyval, "; keycode: ", keycode, "; modifier:", state)
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
	window.FeedCache.StopUpdating()
	window.StopPlaying()
	window.Application().Quit()
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

func (window *AppWindow) PollForMedia() bool {
	if !window.Profile.WarmUpMusic.Exists {
		window.Profile.WarmUpMusic.Refresh()
	}
	window.MainPanel.SetWarmUpButtonSensitive()
	if !window.FeedCache.BaseDirExists {
		window.FeedCache.Refresh()
	}
	window.VideoIndexPanel.RefreshDownloadStateIcons()
	if window.Profile.WarmUpMusic.Exists && window.FeedCache.BaseDirExists {
		return false // No need to call us again
	}
	return true
}

func (window *AppWindow) PollOsmc() bool {
	event := window.Osmc.Poll()
	if event != nil {
		switch event.KeyCode {
		case osmc.KeyBack:
			window.OnBackKey()
		case osmc.KeyPlayPause:
			window.OnPlayPause()
		case osmc.KeyStop:
			window.StopPlaying()
			window.OnBackKey()
		}
	}
	return true
}

func (window *AppWindow) StopPlaying() {
	switch window.Stack.VisibleChildName() {
	case WarmUpPanelName:
		window.WarmUpPanel.Stop()
	case SessionPanelName:
		window.SessionPanel.Stop()
	}
}

func (window *AppWindow) VideoCacheDirectoryUpdated() {
	// A function to be called when the configuration is updated
	window.FeedCache.StopUpdating()
	window.FeedCache = feed.NewFeedCache(window.Profile)
	window.VideoIndexPanel.RefreshDownloadStateIcons()
}
