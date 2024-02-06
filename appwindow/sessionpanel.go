package appwindow

import (
	"fmt"
	"nsw42/picave/feed"
	"nsw42/picave/players"
	"nsw42/picave/widgets"
	"path/filepath"

	"github.com/diamondburned/gotk4/pkg/cairo"
	"github.com/diamondburned/gotk4/pkg/glib/v2"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type SessionPanel struct {
	Parent         *AppWindow
	Contents       *gtk.Box
	VideoArea      *gtk.DrawingArea
	IntervalWidget *widgets.IntervalWidget
	Session        *feed.SessionDefinition
	VideoFile      string
	Realized       bool
	SizeKnown      bool
	Player         players.Player
	TimerHandle    glib.SourceHandle
}

func NewSessionPanel(parent *AppWindow) *SessionPanel {
	rtn := &SessionPanel{Parent: parent, VideoFile: "", Realized: false, SizeKnown: false}

	rtn.VideoArea = gtk.NewDrawingArea()
	// rtn.VideoArea.SetDrawFunc(rtn.OnDraw)
	rtn.VideoArea.ConnectRealize(rtn.OnRealized)
	rtn.VideoArea.ConnectResize(rtn.OnResized)
	rtn.VideoArea.SetHExpand(true)

	rtn.IntervalWidget = widgets.NewIntervalWidget(parent.Profile)
	rtn.IntervalWidget.SetSizeRequest(256, -1)
	rtn.IntervalWidget.SetHExpand(false)

	rtn.Contents = gtk.NewBox(gtk.OrientationHorizontal, 0)
	rtn.Contents.SetHomogeneous(false)
	rtn.Contents.Append(rtn.VideoArea)
	rtn.Contents.Append(rtn.IntervalWidget)

	return rtn
}

func (panel *SessionPanel) OnDraw(_ *gtk.DrawingArea, cr *cairo.Context, width, height int) {
	cr.SetSourceRGB(0, 0, 0)
	cr.Paint()
}

func (panel *SessionPanel) OnRealized() {
	panel.Realized = true
	panel.StartPlayingIfAllPrerequisitesAvailable()
}

func (panel *SessionPanel) OnResized(width int, height int) {
	panel.SizeKnown = true
	// This might be the final event allowing us to actually start playback,
	// or it might be a size change when we're already playing
	if panel.Player != nil {
		// TODO: inform the player of the window size change
	} else {
		panel.StartPlayingIfAllPrerequisitesAvailable()
	}
}

func (panel *SessionPanel) OnTimerTick() bool {
	if panel.Player == nil || panel.Player.IsFinished() {
		panel.Stop()
		panel.Parent.Stack.SetVisibleChildName(VideoIndexPanelName)
		return false
	}
	return true
}

func (panel *SessionPanel) Play(session *feed.SessionDefinition) {
	panel.Session = session
	panel.VideoFile = panel.Parent.FeedCache.Path[session.VideoId]
	if panel.VideoFile == "" {
		fmt.Println("No local video file found for video id: " + session.VideoId)
		return
	}
	panel.Player = players.CreatePlayerForExt(panel.Parent.Profile, filepath.Ext(panel.VideoFile))
	if panel.Player == nil {
		return
	}
	panel.StartPlayingIfAllPrerequisitesAvailable()
}

func (panel *SessionPanel) StartPlayingIfAllPrerequisitesAvailable() {
	if panel.VideoFile != "" && panel.Realized {
		panel.Player.Play(panel.VideoFile)
		panel.IntervalWidget.StartPlaying(panel.Session)
		panel.TimerHandle = glib.TimeoutSecondsAdd(1, panel.OnTimerTick)
	}
}

func (panel *SessionPanel) Stop() {
	glib.SourceRemove(panel.TimerHandle)
	if panel.Player != nil {
		panel.Player.Stop()
	}
	panel.Player = nil
	panel.VideoFile = ""
}
