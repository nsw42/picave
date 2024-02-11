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
	BlankVideoArea *gtk.DrawingArea
	IntervalWidget *widgets.IntervalWidget
	Session        *feed.SessionDefinition
	VideoFile      string
	Realized       bool
	SizeKnown      bool
	Player         players.VideoPlayer
	TimerHandle    glib.SourceHandle
}

func NewSessionPanel(parent *AppWindow) *SessionPanel {
	rtn := &SessionPanel{Parent: parent, VideoFile: "", Realized: false, SizeKnown: false}

	rtn.BlankVideoArea = gtk.NewDrawingArea()
	rtn.BlankVideoArea.SetDrawFunc(rtn.OnDraw)
	rtn.BlankVideoArea.ConnectResize(rtn.OnResized)
	rtn.BlankVideoArea.SetHExpand(true)

	rtn.IntervalWidget = widgets.NewIntervalWidget(parent.Profile)
	rtn.IntervalWidget.SetSizeRequest(256, -1)
	rtn.IntervalWidget.SetHExpand(false)

	rtn.Contents = gtk.NewBox(gtk.OrientationHorizontal, 0)
	rtn.Contents.SetHomogeneous(false)
	rtn.Contents.Append(rtn.BlankVideoArea)
	rtn.Contents.Append(rtn.IntervalWidget)

	rtn.Contents.ConnectRealize(rtn.OnRealized)

	return rtn
}

func (panel *SessionPanel) OnDraw(_ *gtk.DrawingArea, cr *cairo.Context, width, height int) {
	cr.SetSourceRGB(0, 0, 0)
	cr.Paint()
}

func (panel *SessionPanel) OnPlayPause() {
	panel.Player.PlayPause()
	panel.IntervalWidget.PlayPause()
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
	if panel.Player == nil || panel.Player.PlayerState() == players.PlayerFinished {
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
	panel.Player = players.CreateVideoPlayerForExt(panel.Parent.Profile, filepath.Ext(panel.VideoFile))
	if panel.Player == nil {
		return
	}
	panel.StartPlayingIfAllPrerequisitesAvailable()
}

func (panel *SessionPanel) StartPlayingIfAllPrerequisitesAvailable() {
	if panel.VideoFile != "" && panel.Realized {
		// Skipping starting video in the event of a missing player means that we add the timer,
		// which causes us to stop and jump back to the index. If we skip this entire block,
		// people are just faced with a blank window.
		if panel.Player != nil {
			panel.Player.Play(panel.VideoFile, &panel.BlankVideoArea.Widget)
		}
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
