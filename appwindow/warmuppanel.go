package appwindow

import (
	_ "embed"
	"fmt"
	"nsw42/picave/players"
	"nsw42/picave/utils"
	"os"
	"time"

	"github.com/dhowden/tag"
	"github.com/diamondburned/gotk4/pkg/gdk/v4"
	"github.com/diamondburned/gotk4/pkg/glib/v2"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
	"github.com/tcolgate/mp3"
)

type WarmUpPanel struct {
	Parent          *AppWindow
	Contents        *gtk.Grid
	ArtistLabel     *gtk.Label
	TitleLabel      *gtk.Label
	TimeLabel       *gtk.Label
	DurationLabel   *gtk.Label
	Pad             *gtk.Fixed
	NextButton      *gtk.Button
	BackButton      *gtk.Button
	TimerHandle     glib.SourceHandle
	MusicPlayer     players.Player
	PlayerStartedAt time.Time
}

type MusicFileMetadata struct {
	Filetype        string
	Artist          string
	Title           string
	DurationSeconds int
}

const (
	MP3 = ".mp3"
	MP4 = ".mp4"
	MKV = ".mkv"
)

//go:embed "warmuppanel.css"
var WarmUpPanelCss string

func NewWarmUpPanel(parent *AppWindow) *WarmUpPanel {
	rtn := &WarmUpPanel{Parent: parent}

	rtn.ArtistLabel = expandingLabel("<artist>", "artist-label")
	rtn.TitleLabel = expandingLabel("<title>", "title-label")
	rtn.TimeLabel = expandingLabel("<time>", "time-label")
	rtn.TimeLabel.SetHAlign(gtk.AlignEnd)
	rtn.DurationLabel = expandingLabel("/ <duration>", "time-label")
	rtn.DurationLabel.SetHAlign(gtk.AlignStart)

	cssProvider := gtk.NewCSSProvider()
	cssProvider.LoadFromData(WarmUpPanelCss)
	gtk.StyleContextAddProviderForDisplay(gdk.DisplayGetDefault(), cssProvider, gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

	timeHBox := gtk.NewBox(gtk.OrientationHorizontal, 0)
	timeHBox.Append(rtn.TimeLabel)
	timeHBox.Append(rtn.DurationLabel)

	rtn.Pad = gtk.NewFixed()

	rtn.NextButton = gtk.NewButtonWithLabel("Next track")
	rtn.NextButton.SetVExpand(false)
	rtn.NextButton.ConnectClicked(rtn.OnNextButtonClicked)
	rtn.BackButton = gtk.NewButtonWithLabel("Back")
	rtn.BackButton.SetHExpand(true)
	rtn.BackButton.SetSizeRequest(0, 80) // width is set by grid
	rtn.BackButton.ConnectClicked(rtn.OnBackClicked)

	//       0         1             2
	//  0            artist
	//  1   pad      title          Next
	//  2        time/duration
	//  3            Back

	grid := gtk.NewGrid()
	// row 0: artist
	grid.Attach(rtn.ArtistLabel, 1, 0, 1, 1)
	// row 1: pad, title, next
	grid.Attach(rtn.Pad, 0, 1, 1, 1)
	grid.Attach(rtn.TitleLabel, 1, 1, 1, 1)
	grid.Attach(rtn.NextButton, 2, 1, 1, 1)
	// row 2: time/duration (in the hbox)
	grid.Attach(timeHBox, 1, 2, 1, 1)
	// roe 3: back
	grid.Attach(rtn.BackButton, 1, 3, 1, 1)
	grid.SetMarginTop(200)
	grid.SetMarginBottom(200)
	grid.SetMarginStart(200)
	grid.SetMarginEnd(200)
	rtn.Contents = grid

	grid.ConnectRealize(rtn.OnRealized)

	return rtn
}

func (panel *WarmUpPanel) OnBackClicked() {
	glib.SourceRemove(panel.TimerHandle)
	panel.MusicPlayer.Stop()
	panel.Parent.Stack.SetVisibleChildName(MainPanelName)
}

func (panel *WarmUpPanel) OnNextButtonClicked() {
	panel.MusicPlayer.Stop()
	panel.PlayRandomTrack()
}

func (panel *WarmUpPanel) OnRealized() {
	panel.NextButton.GrabFocus()
}

func (panel *WarmUpPanel) OnShown() {
	_, naturalSize := panel.NextButton.PreferredSize()
	naturalSize.Width()
	panel.Pad.SetSizeRequest(naturalSize.Width(), 32)

	panel.PlayRandomTrack()
	panel.TimerHandle = glib.TimeoutSecondsAdd(1, panel.OnTimerTick)
}

func (panel *WarmUpPanel) OnTimerTick() bool {
	if panel.MusicPlayer == nil {
		return false
	}
	if panel.MusicPlayer.IsFinished() {
		panel.PlayRandomTrack()
	} else {
		musicTrackElapsed := time.Since(panel.PlayerStartedAt)
		panel.TimeLabel.SetLabel(utils.FormatDurationMMSS(musicTrackElapsed))
	}
	return true
}

func (panel *WarmUpPanel) PlayRandomTrack() {
	musicFile := panel.Parent.Profile.WarmUpMusic.PickRandomFile()
	metadata := getMusicFileInfo(musicFile)

	panel.ArtistLabel.SetLabel(metadata.Artist)
	panel.TitleLabel.SetLabel(metadata.Title)
	if metadata.DurationSeconds == 0 {
		panel.TimeLabel.SetLabel("")
		panel.DurationLabel.SetLabel("")
	} else {
		mm := int(metadata.DurationSeconds / 60.)
		ss := int(metadata.DurationSeconds - mm*60.0)
		panel.DurationLabel.SetLabel(fmt.Sprintf("/ %02d:%02d", mm, ss))
	}

	if panel.MusicPlayer == nil {
		panel.MusicPlayer = players.CreatePlayerForExt(panel.Parent.Profile, metadata.Filetype)
	}
	panel.MusicPlayer.Play(musicFile)
	panel.PlayerStartedAt = time.Now()
}

func expandingLabel(contents string, cssClass string) *gtk.Label {
	label := gtk.NewLabel(contents)
	label.SetHExpand(true)
	label.SetVExpand(true)
	label.AddCSSClass(cssClass)
	return label
}

func getMusicFileInfo(musicFile string) MusicFileMetadata {
	handle, err := os.Open(musicFile)
	if err != nil {
		return MusicFileMetadata{}
	}
	defer handle.Close()
	metadata, err := tag.ReadFrom(handle)
	if err != nil {
		return MusicFileMetadata{}
	}
	filetype := ""
	artist := metadata.Artist()
	title := metadata.Title()
	duration := 0.0
	switch metadata.Format() {
	case tag.ID3v1, tag.ID3v2_2, tag.ID3v2_3, tag.ID3v2_4:
		// This taken from StackOverflow: https://stackoverflow.com/questions/60281655/how-to-find-the-length-of-mp3-file-in-golang
		// but it seems inconveniently slow, having to decode the entire file. Would be good to find an alternative.
		filetype = MP3
		decoder := mp3.NewDecoder(handle)
		var frame mp3.Frame
		var skipped int
		for {
			if err := decoder.Decode(&frame, &skipped); err != nil {
				break
			}
			duration += frame.Duration().Seconds()
		}
	}
	return MusicFileMetadata{filetype, artist, title, int(duration)}
}
