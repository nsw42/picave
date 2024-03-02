package players

import (
	"encoding/json"
	"fmt"
	"log"
	"nsw42/picave/profile"
	"os/exec"

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

func getVideoSize(filepath string) (int, int) {
	cmd := exec.Command("ffprobe", "-v", "error", "-print_format", "json", "-select_streams", "v:0", "-show_entries", "stream=width,height", filepath)
	output, err := cmd.Output()
	if err != nil {
		return 0, 0
	}
	var outputMap map[string]any
	if json.Unmarshal(output, &outputMap) != nil {
		return 0, 0
	}
	streams := outputMap["streams"].([]any)
	stream := streams[0]
	streamMap := stream.(map[string]any)
	width := int(streamMap["width"].(float64))
	height := int(streamMap["height"].(float64))
	return width, height
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

	videoW, videoH := getVideoSize(filepath)
	log.Println("Video size: ", videoW, "x", videoH)

	widthRatio := float64(windowW) / float64(videoW)
	heightRatio := float64(windowH) / float64(videoH)

	drawRatio := min(widthRatio, heightRatio)

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
