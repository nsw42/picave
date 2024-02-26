package main

import (
	"errors"
	"fmt"
	"nsw42/picave/appwindow"
	"nsw42/picave/osmc"
	"nsw42/picave/profile"
	"nsw42/picave/profilechooser"
	"os"
	"os/user"
	"path"

	"github.com/akamensky/argparse"
	"github.com/diamondburned/gotk4/pkg/gio/v2"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type Arguments struct {
	ProfilePath        string
	Fullscreen         bool
	RunOsmcTest        bool
	OsmcPath           string
	DeveloperMode      bool
	ShowProfileChooser bool
}

var args Arguments
var appWindow *appwindow.AppWindow

func validateOptionFileExists(args []string) error {
	_, err := os.Stat(args[0])
	if errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("file '%s' does not exist", args[0])
	}
	return nil
}

func parseArgs() bool {
	user, err := user.Current()
	var defaultConfigFile string
	if err == nil {
		defaultConfigFile = path.Join(user.HomeDir, ".picaverc")
	} else {
		defaultConfigFile = ".picaverc" // Just look in current working directory
	}
	parser := argparse.NewParser("picave", "A GTK-based personal trainer for cyclists")
	osmcPathArg := parser.String("o", "osmc", &argparse.Options{Help: "Path to the OSMC device", Default: ""})
	osmcTestArg := parser.Flag("O", "osmctest", &argparse.Options{Help: "Run the OSMC test", Default: false})
	profileArg := parser.String("p", "profile", &argparse.Options{Help: "Profile file to read. If used in conjunction with --show-profile-chooser, the profile to select in the window", Default: defaultConfigFile, Validate: validateOptionFileExists})
	chooserArg := parser.Flag("c", "show-profile-chooser", &argparse.Options{Help: "Show the profile chooser at launch"})
	fullscreenArg := parser.Flag("", "fullscreen", &argparse.Options{Default: false, Help: "Run the application full-screen"})
	developerModeArg := parser.Flag("d", "developer", &argparse.Options{Help: "Enable developer mode. Include things like the video id in the index panel"})

	if err := parser.Parse(os.Args); err != nil {
		fmt.Println(err)
		return false
	}

	args.ProfilePath = *profileArg
	args.Fullscreen = *fullscreenArg
	args.RunOsmcTest = *osmcTestArg
	args.OsmcPath = *osmcPathArg
	args.DeveloperMode = *developerModeArg
	args.ShowProfileChooser = *chooserArg

	return true
}

func main() {
	if !parseArgs() {
		return
	}

	if args.RunOsmcTest {
		osmc.RunTest(args.OsmcPath)
		return
	}

	app := gtk.NewApplication("com.github.nsw42.picave", gio.ApplicationFlagsNone)
	app.ConnectActivate(func() { activate(app) })
	app.Run([]string{})
	if appWindow != nil && appWindow.FeedCache != nil {
		appWindow.FeedCache.StopUpdating()
	}
}

func activate(app *gtk.Application) {
	if args.ShowProfileChooser {
		chooser := profilechooser.NewProfileChooserWindow(app,
			args.ProfilePath,
			func(profilePath string) {
				showMainWindow(app, profilePath)
			})
		chooser.Show()
	} else {
		showMainWindow(app, args.ProfilePath)
	}
}

func showMainWindow(app *gtk.Application, profilePath string) {
	prf, err := profile.LoadProfile(profilePath)
	if err != nil {
		var pErr *os.PathError
		if errors.As(err, &pErr) {
			// No such file or directory (probably)
			fmt.Println("Warning: Couldn't read profile path ", profilePath, ":", err)
			prf = profile.DefaultProfile(profilePath)
		} else {
			fmt.Println("Profile file validation failed: ", err)
			return
		}
	}
	appWindow = appwindow.NewAppWindow(app, prf, args.Fullscreen, args.DeveloperMode)
	appWindow.GtkWindow.Show()
}
