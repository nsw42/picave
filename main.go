package main

import (
	"errors"
	"fmt"
	"nsw42/picave/appwindow"
	"nsw42/picave/osmc"
	"nsw42/picave/profile"
	"os"
	"os/user"
	"path"

	"github.com/akamensky/argparse"
	"github.com/diamondburned/gotk4/pkg/gio/v2"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type Arguments struct {
	Profile     *profile.Profile
	Fullscreen  bool
	RunOsmcTest bool
	OsmcPath    string
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
	profileArg := parser.String("p", "profile", &argparse.Options{Help: "Profile file to read", Default: defaultConfigFile, Validate: validateOptionFileExists})
	fullscreenArg := parser.Flag("", "fullscreen", &argparse.Options{Default: false, Help: "Run the application full-screen"})

	if err := parser.Parse(os.Args); err != nil {
		fmt.Println(err)
		return false
	}

	args.Profile, err = profile.LoadProfile(*profileArg)
	if err != nil {
		var pErr *os.PathError
		if errors.As(err, &pErr) {
			// No such file or directory (probably)
			args.Profile = profile.DefaultProfile(*profileArg)
		} else {
			fmt.Println("Profile file validation failed: ", err)
			return false
		}
	}

	args.Fullscreen = *fullscreenArg
	args.RunOsmcTest = *osmcTestArg
	args.OsmcPath = *osmcPathArg

	return true
}

func main() {
	if !parseArgs() {
		return
	}

	if args.RunOsmcTest {
		osmc.RunTest(args.OsmcPath, true) // TODO: Make this debounce optional?
		return
	}

	app := gtk.NewApplication("com.github.nsw42.picave", gio.ApplicationFlagsNone)
	app.ConnectActivate(func() { activate(app) })
	app.Run([]string{})
	appWindow.FeedCache.StopUpdating()
}

func activate(app *gtk.Application) {
	appWindow = appwindow.NewAppWindow(app, args.Profile, args.Fullscreen)
	appWindow.GtkWindow.Show()
}
