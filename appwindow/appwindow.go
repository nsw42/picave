package appwindow

import (
	"github.com/diamondburned/gotk4/pkg/gdk/v4"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type AppWindow struct {
	GtkWindow   *gtk.ApplicationWindow
	Stack       *gtk.Stack
	MainPanel   *MainPanel
	WarmUpPanel *WarmUpPanel
}

func NewAppWindow(app *gtk.Application,
	fullScreen bool,
) *AppWindow {
	rtn := &AppWindow{}
	rtn.GtkWindow = gtk.NewApplicationWindow(app)
	rtn.GtkWindow.SetTitle("PiCave")

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

	rtn.Stack.AddNamed(rtn.MainPanel.Contents, MainPanelName)
	rtn.Stack.AddNamed(rtn.WarmUpPanel.Contents, WarmUpPanelName)

	rtn.Stack.SetVisibleChildName(MainPanelName)

	return rtn
}
