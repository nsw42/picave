package appwindow

import (
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
