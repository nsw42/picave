package widgets

import (
	"fmt"
	"nsw42/picave/feed"
	"nsw42/picave/profile"
	"nsw42/picave/utils"
	"time"

	"github.com/diamondburned/gotk4/pkg/cairo"
	"github.com/diamondburned/gotk4/pkg/glib/v2"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type DrawInterval struct {
	feed.IntervalDefinition
	StartOffset time.Duration
	EndOffset   time.Duration
	EffortStr   string
}

type IntervalWidget struct {
	*gtk.DrawingArea
	Profile              *profile.Profile
	Session              *feed.SessionDefinition
	PlayerStartTime      time.Time
	DrawIntervals        []DrawInterval
	CurrentIntervalIndex int
}

const (
	TextXPos        = 8
	TextHeight      = 30
	TextBlockHeight = TextHeight * 4
)

func NewIntervalWidget(profile *profile.Profile) *IntervalWidget {
	rtn := &IntervalWidget{gtk.NewDrawingArea(), profile, nil, time.Time{}, []DrawInterval{}, -1}
	rtn.SetDrawFunc(rtn.OnDraw)
	return rtn
}

func (widget *IntervalWidget) ForceRedraw() bool {
	if widget.CurrentIntervalIndex < 0 {
		return false
	}
	widget.QueueDraw()
	return true
}

func (widget *IntervalWidget) StartPlaying(session *feed.SessionDefinition) {
	widget.Session = session
	widget.DrawIntervals = []DrawInterval{}
	startOffset := time.Duration(0)
	videoFTP := float64(widget.Profile.GetVideoFTPVal(session.VideoId, true))
	videoMaxInt := widget.Profile.GetVideoMaxVal(session.VideoId, true)
	var videoMaxStr string
	if videoMaxInt == 0 {
		videoMaxStr = "MAX"
	} else {
		videoMaxStr = fmt.Sprintf("%d%%", videoMaxInt)
	}
	for _, feedInterval := range session.Intervals {
		var intervalEffort float64
		var intervalEffortStr string
		switch feedInterval.Effort.Type {
		case feed.RelativeToFTPValue:
			intervalEffort = float64(feedInterval.Effort.PercentFTP) * videoFTP / 100.0
			intervalEffortStr = fmt.Sprintf("%dW", int(intervalEffort))
		case feed.MaxEffort:
			intervalEffortStr = videoMaxStr
		}
		widget.DrawIntervals = append(widget.DrawIntervals,
			DrawInterval{
				feedInterval,
				startOffset,
				startOffset + feedInterval.Duration.Duration,
				intervalEffortStr})
		startOffset += feedInterval.Duration.Duration
	}
	widget.CurrentIntervalIndex = 0
	widget.PlayerStartTime = time.Now()
	glib.TimeoutAdd(200, widget.ForceRedraw)
}

func (widget *IntervalWidget) OnDraw(area *gtk.DrawingArea, cr *cairo.Context, width, height int) {
	if widget.Session == nil {
		cr.SetSourceRGB(0, 0, 0)
		cr.Paint()
		return
	}

	now := time.Now()
	intervals := widget.DrawIntervals
	for widget.CurrentIntervalIndex < len(intervals) &&
		now.After(widget.PlayerStartTime.Add(intervals[widget.CurrentIntervalIndex].EndOffset)) {
		widget.CurrentIntervalIndex++
	}

	endY := 0.0
	oneMinuteHeight := float64(area.AllocatedHeight() - TextBlockHeight)
	oneSecondHeight := oneMinuteHeight / 60.

	drawW := float64(area.AllocatedWidth())

	cr.SelectFontFace("Sans", cairo.FontSlantNormal, cairo.FontWeightNormal)
	cr.SetAntialias(cairo.AntialiasDefault)
	cr.SetFontSize(24)

	for drawIndex, drawInterval := range intervals[widget.CurrentIntervalIndex:] {
		var drawIntervalRemaining time.Duration
		var rectY, rectH, textY float64
		if drawIndex == 0 {
			// 0 => current interval, not necessarily the first in the session
			drawIntervalEnd := widget.PlayerStartTime.Add(drawInterval.EndOffset)
			drawIntervalRemaining = drawIntervalEnd.Sub(now)
			rectY = 0
			rectH = drawIntervalRemaining.Seconds() * oneSecondHeight
			textY = min(0, rectH-TextBlockHeight-8) + TextHeight
		} else {
			drawIntervalRemaining = drawInterval.Duration.Duration
			intervalStartTime := widget.PlayerStartTime.Add(drawInterval.StartOffset)
			startDelta := intervalStartTime.Sub(now)
			rectY = startDelta.Seconds() * oneSecondHeight
			rectH = drawIntervalRemaining.Seconds() * oneSecondHeight
			textY = rectY + TextHeight
		}

		cr.Rectangle(0, rectY, drawW, rectH)
		cr.SetSourceRGB(drawInterval.Color.Red, drawInterval.Color.Green, drawInterval.Color.Blue)
		cr.FillPreserve()
		cr.SetSourceRGB(0, 0, 0)
		cr.Stroke()

		cr.MoveTo(TextXPos, textY)
		cr.ShowText(drawInterval.Name)
		textY += TextHeight

		cr.MoveTo(TextXPos, textY)
		cr.ShowText(drawInterval.EffortStr)
		textY += TextHeight

		cr.MoveTo(TextXPos, textY)
		cr.ShowText(fmt.Sprintf("RPM: %d", drawInterval.Cadence))
		textY += TextHeight

		cr.MoveTo(TextXPos, textY)
		cr.ShowText(utils.FormatDurationMMSS(drawIntervalRemaining))
		textY += TextHeight

		endY = rectY + rectH
	}

	cr.SetSourceRGB(0, 0, 0)
	cr.Rectangle(0, endY, drawW, float64(area.AllocatedHeight())-endY)
	cr.FillPreserve()
}
