package main

import (
	"errors"
	"fmt"
	"nsw42/picave/appwindow"
	"nsw42/picave/profile"
	"os"

	"github.com/akamensky/argparse"
	"github.com/diamondburned/gotk4/pkg/gio/v2"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type Arguments struct {
	Profile    *profile.Profile
	Fullscreen bool
}

var args Arguments
var appWindow *appwindow.AppWindow

func validateOptionFileExists(args []string) error {
	_, err := os.Stat(args[0])
	if errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("File '%s' does not exist", args[0])
	}
	return nil
}

func parseArgs() bool {
	parser := argparse.NewParser("picave", "A GTK-based personal trainer for cyclists")
	ProfileArg := parser.String("p", "profile", &argparse.Options{Help: "Profile file to read", Validate: validateOptionFileExists})
	fullscreenArg := parser.Flag("", "fullscreen", &argparse.Options{Default: false, Help: "Run the application full-screen"})

	if err := parser.Parse(os.Args); err != nil {
		fmt.Println(err)
		return false
	}

	var err error
	args.Profile, err = profile.LoadProfile(*ProfileArg)
	if err != nil {
		fmt.Println("Profile file validation failed: ", err)
		return false
	}

	args.Fullscreen = *fullscreenArg

	return true
}

func main() {
	if !parseArgs() {
		return
	}

	app := gtk.NewApplication("com.github.nsw42.picave", gio.ApplicationFlagsNone)
	app.ConnectActivate(func() { activate(app) })
	app.Run([]string{})
}

func activate(app *gtk.Application) {
	appWindow = appwindow.NewAppWindow(app, args.Profile, args.Fullscreen)
	appWindow.GtkWindow.Show()
}
