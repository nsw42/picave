//go:build ignore

// This looks vaguely promising - except for the build errors in the gotk4-gstreamer package that I can't be bothered to fight with right now

package players

import (
	"fmt"
	"nsw42/picave/profile"
	"os"

	coregst "github.com/OmegaRogue/gotk4-gstreamer/pkg/core/gst"
	"github.com/OmegaRogue/gotk4-gstreamer/pkg/gst"
	"github.com/OmegaRogue/gotk4-gstreamer/pkg/gstapp"

	"github.com/diamondburned/gotk4/pkg/gdk/v4"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type GtkVideoPlayer struct {
	Profile    *profile.Profile
	State      PlayerState
	GtkPicture *gtk.Picture

	GStreamerSource  *gstapp.AppSrc
	GStreamerConvert gst.Elementer
	GStreamerSink    gst.Elementer
}

func (player *GtkVideoPlayer) PlayerState() PlayerState {
	return player.State
}

func (player *GtkVideoPlayer) Play(filename string) *gtk.Widget {
	// Based heavily on https://github.com/OmegaRogue/gotk4-gstreamer/blob/develop/pkg/_examples/basic/main.go
	if player.GtkPicture == nil {
		gst.Init()
		player.GStreamerSource = gst.ElementFactoryMake("appsrc", "source").(*gstapp.AppSrc)
		player.GStreamerConvert = gst.ElementFactoryMake("videoconvert", "convert")
		player.GStreamerSink = gst.ElementFactoryMake("gtk4paintablesink", "sink")

		pipeline := gst.NewPipeline("test-pipeline")
		pipeline.AddMany(player.GStreamerSource, player.GStreamerConvert, player.GStreamerSink)
		coregst.ElementLinkMany(player.GStreamerSource, player.GStreamerConvert, player.GStreamerSink)

		paintable := player.GStreamerSink.ObjectProperty("paintable").(gdk.Paintabler)

		player.GtkPicture = gtk.NewPicture()
		player.GtkPicture.SetPaintable(paintable)
	}

	file, _ := os.OpenFile(filename, os.O_RDONLY, 0644)
	player.GStreamerSource.ConnectNeedData(func(length uint) {
		// io.Copy(source, file)
		fmt.Println("Copy", length, "bytes from ", file)
	})

	return &player.GtkPicture.Widget
}

func (player *GtkVideoPlayer) PlayPause() {
	// TODO
	if player.State == PlayerPlaying {
		player.State = PlayerPaused
	} else {
		player.State = PlayerPlaying
	}
}

func (player *GtkVideoPlayer) Stop() {
	player.State = PlayerFinished
}

func NewGtkVideoPlayer(profile *profile.Profile) VideoPlayer {
	return &GtkVideoPlayer{profile, PlayerNotStarted, nil, nil, nil, nil}
}

func init() {
	registerVideoPlayer("gtk", NewGtkVideoPlayer)
}
