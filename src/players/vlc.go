//go:build ignore

package players

/*
#cgo CFLAGS: -x objective-c
#cgo CFLAGS: -I/Applications/VLC.app/Contents/MacOS/include
#cgo LDFLAGS: -L/Applications/VLC.app/Contents/MacOS/lib
#cgo pkg-config: gdk-3.0
#include <AppKit/AppKit.h>
#include <gdk/gdk.h>
GDK_AVAILABLE_IN_ALL NSView* gdk_quartz_window_get_nsview(GdkWindow *window);
*/
import "C"

// Runtime: export DYLD_LIBRARY_PATH=/lib:/Applications/VLC.app/Contents/MacOS/lib

import (
	"fmt"
	"log"
	"nsw42/picave/profile"
	"os/exec"
	"unsafe"

	vlc "github.com/adrg/libvlc-go/v3"
	"github.com/diamondburned/gotk4/pkg/gdk/v4"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

func init() {
	if err := vlc.Init(); err != nil {
		log.Fatal("VLC:", err)
	}
	// vlc.Release?
}

type VlcPlayer struct {
	State   PlayerState
	Profile *profile.Profile
	Command *exec.Cmd
	Vlc     *vlc.Player
}

func NewVlcPlayer(profile *profile.Profile, options *profile.FiletypePlayerOptions) VideoPlayer {
	return &VlcPlayer{PlayerNotStarted, profile, nil, nil}
}

func init() {
	registerVideoPlayer("vlc", NewVlcPlayer)
}

func (player *VlcPlayer) PlayerState() PlayerState {
	return player.State
}

func (player *VlcPlayer) Play(file string, parent *gtk.Widget) *gtk.Widget {
	drawingArea := gtk.NewDrawingArea()
	drawingArea.SetParent(parent)
	drawingArea.ConnectRealize(func() {
		surface := drawingArea.Native().Surface().(*gdk.Surface)
		fmt.Printf("Surface: %p\n", surface)
		if surface != nil {
			object := surface.Object
			fmt.Println("Object:", object)
			window := (*C.GdkWindow)(unsafe.Pointer(surface.Object))
			fmt.Printf("Window: %p\n", window)
			if window != nil {
				handle := unsafe.Pointer(C.gdk_quartz_window_get_nsview(window))
				if uintptr(handle) != 0 {
					player.Vlc.SetNSObject(uintptr(handle))
				}
			}
		}
	})
	go player.launch(file)
	return &drawingArea.Widget
}

func (player *VlcPlayer) PlayPause() {
	if player.Vlc != nil {
		player.Vlc.TogglePause()
	}
}

func (player *VlcPlayer) Stop() {
	if player.Vlc != nil {
		player.Vlc.Stop()
	}
}

func (player *VlcPlayer) launch(file string) {
	vlcPlayer, err := vlc.NewPlayer()
	if err != nil {
		log.Println("Unable to launch VLC")
		player.State = PlayerFinished
		return
	}
	player.Vlc = vlcPlayer
	media, err := vlcPlayer.LoadMediaFromPath(file)
	if err != nil {
		log.Println("Unable to open media " + file)
		player.State = PlayerFinished
		return
	}
	defer media.Release()

	player.State = PlayerPlaying
	vlcPlayer.Play()
	player.State = PlayerFinished
}
