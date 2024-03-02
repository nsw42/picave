package widgets

import (
	"math"
	"nsw42/picave/feed"
	"nsw42/picave/profile"
	"sort"

	"github.com/diamondburned/gotk4/pkg/cairo"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type PreviewInterval struct {
	feed.IntervalDefinition
	DurationSec float64
	EffortVal   float64
	StartOffset float64
}

type SessionPreview struct {
	*gtk.DrawingArea
	Profile            *profile.Profile
	Session            *feed.SessionDefinition
	DrawOrderIntervals []PreviewInterval
	MaxDuration        float64
}

func NewSessionPreview(profile *profile.Profile) *SessionPreview {
	rtn := &SessionPreview{gtk.NewDrawingArea(), profile, nil, []PreviewInterval{}, 0}
	rtn.SetDrawFunc(rtn.OnDraw)
	return rtn
}

func (widget *SessionPreview) OnDraw(_ *gtk.DrawingArea, cr *cairo.Context, width, height int) {
	if widget.MaxDuration == 0 {
		return
	}
	drawW := float64(widget.AllocatedWidth())
	drawH := float64(widget.AllocatedHeight())
	drawXScale := drawW / widget.MaxDuration

	// Draw effort rectangles
	for _, interval := range widget.DrawOrderIntervals {
		x := interval.StartOffset * drawXScale
		w := interval.DurationSec * drawXScale
		cr.SetSourceRGB(interval.Color.Red, interval.Color.Green, interval.Color.Blue)
		cr.Rectangle(x, 0, w, drawH)
		cr.FillPreserve()
		cr.Stroke()
	}

	// Now overdraw cadence line
	for _, interval := range widget.DrawOrderIntervals {
		x := interval.StartOffset * drawXScale
		w := interval.DurationSec * drawXScale
		// cadence y scaling: max_y=40, min_y=130
		y := float64(max(0, 130-interval.Cadence)) * drawH / (130 - 40)
		cr.SetSourceRGB(0, 0, 0)
		cr.SetLineWidth(3)
		cr.MoveTo(x, y)
		cr.LineTo(x+w, y)
		cr.Stroke()
	}
}

func (widget *SessionPreview) ShowSession(session *feed.SessionDefinition) {
	widget.Session = session
	if session == nil {
		widget.DrawOrderIntervals = []PreviewInterval{}
		return
	}
	// intervals are given to us in chronological order, but sort them
	// into desired order for drawing
	widget.DrawOrderIntervals = make([]PreviewInterval, len(session.Intervals))
	videoFTP := float64(widget.Profile.GetVideoFTPVal(session.VideoId, true))
	videoMaxInt := widget.Profile.GetVideoMaxVal(session.VideoId, true)
	var videoMax float64
	if videoMaxInt == 0 {
		videoMax = math.Inf(1)
	} else {
		videoMax = float64(videoMaxInt)
	}
	// Initially, construct the intervals in chronological order (the same as the underlying session intervals)
	startOffset := 0.0
	for i, feedInterval := range session.Intervals {
		var intervalEffort float64
		switch feedInterval.Effort.Type {
		case feed.RelativeToFTPValue:
			intervalEffort = float64(feedInterval.Effort.PercentFTP) * videoFTP / 100.0
		case feed.MaxEffort:
			intervalEffort = videoMax
		}
		widget.DrawOrderIntervals[i] = PreviewInterval{feedInterval, feedInterval.Duration.Seconds(), intervalEffort, startOffset}
		startOffset += feedInterval.Duration.Seconds()
	}
	widget.MaxDuration = widget.DrawOrderIntervals[len(widget.DrawOrderIntervals)-1].StartOffset + widget.DrawOrderIntervals[len(widget.DrawOrderIntervals)-1].DurationSec
	sort.Slice(widget.DrawOrderIntervals, func(i, j int) bool {
		if widget.DrawOrderIntervals[i].EffortVal == widget.DrawOrderIntervals[j].EffortVal {
			return widget.DrawOrderIntervals[i].StartOffset < widget.DrawOrderIntervals[j].StartOffset
		}
		return widget.DrawOrderIntervals[i].EffortVal < widget.DrawOrderIntervals[j].EffortVal
	})
	widget.QueueDraw()
}
