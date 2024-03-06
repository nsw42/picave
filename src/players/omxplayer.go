package players

import (
	"fmt"
	"log"
	"nsw42/picave/profile"

	"github.com/basilfx/go-omxplayer"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type OmxPlayer struct {
	Profile *profile.Profile
	Options *profile.FiletypePlayerOptions
	State   PlayerState
	Omx     *omxplayer.Player
}

func init() {
	registerVideoPlayer("omxplayer", NewOmxPlayer)
}

func NewOmxPlayer(profile *profile.Profile, options *profile.FiletypePlayerOptions) VideoPlayer {
	return &OmxPlayer{profile, options, PlayerNotStarted, nil}
}

func (player *OmxPlayer) PlayerState() PlayerState {
	return player.State
}

func (player *OmxPlayer) Play(filepath string, parent *gtk.Widget) *gtk.Widget {
	args := player.Options.Options

	window := parent.Allocation()
	windowX := window.X() + player.Options.Margins.Left
	windowY := window.Y() + player.Options.Margins.Top
	windowW := window.Width() - player.Options.Margins.Left - player.Options.Margins.Right
	windowH := window.Height() - player.Options.Margins.Top - player.Options.Margins.Bottom
	log.Println("Target playback size: ", windowW, "x", windowH, " at ", windowX, ",", windowY)

	drawRatio := getVideoScale(filepath, windowW, windowH)
	videoW, videoH := getVideoSize(filepath) // This duplicates a call to ffprobe, which could be optimised if the delay is noticeable
	drawW := int(float64(videoW) * drawRatio)
	drawH := int(float64(videoH) * drawRatio)

	drawX0 := windowX + (windowW-drawW)/2
	drawY0 := windowY + (windowH-drawH)/2
	drawX1 := drawX0 + drawW
	drawY1 := drawY0 + drawH

	args = append(args, "--win")
	args = append(args, fmt.Sprintf("%d,%d,%d,%d", drawX0, drawY0, drawX1, drawY1))
	args = append(args, "--aspect-mode")
	args = append(args, "letterbox")

	omx, err := omxplayer.New(filepath, args...)
	if err != nil {
		log.Println(err)
		player.State = PlayerFinished
		return nil
	}

	player.Omx = omx
	omx.WaitForReady()
	omx.Play()
	player.State = PlayerPlaying

	return nil
}

func (player *OmxPlayer) PlayPause() {
	if player.Omx != nil {
		player.Omx.PlayPause()
	}
}

func (player *OmxPlayer) Stop() {
	if player.Omx != nil {
		player.Omx.Stop()
	}
}
