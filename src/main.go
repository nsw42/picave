package main

import (
	_ "embed"
	"errors"
	"fmt"
	"nsw42/picave/appwindow"
	"nsw42/picave/osmc"
	"nsw42/picave/profile"
	"nsw42/picave/profilechooser"
	"os"
	"os/user"
	"path"
	"strings"

	"github.com/akamensky/argparse"
	"github.com/diamondburned/gotk4/pkg/gio/v2"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

//go:embed "version.txt"
var Version string

type Application struct {
	*gtk.Application
	Arguments Arguments
}

type Arguments struct {
	ProfilePath        string
	Fullscreen         bool
	RunOsmcTest        bool
	OsmcPath           string
	DeveloperMode      bool
	ShowProfileChooser bool
	HideMousePointer   bool
	ShowVersion        bool
}

var appWindow *appwindow.AppWindow

func validateOptionFileExists(args []string) error {
	_, err := os.Stat(args[0])
	if errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("file '%s' does not exist", args[0])
	}
	return nil
}

func parseArgs() (Arguments, bool) {
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
	hideMousePointerArg := parser.Flag("m", "hide-mouse-pointer", &argparse.Options{Help: "Hide the mouse pointer when it is over the main window"})
	showVersionArg := parser.Flag("V", "version", &argparse.Options{Help: "Show version string and exit"})

	if err := parser.Parse(os.Args); err != nil {
		fmt.Println(err)
		return Arguments{}, false
	}

	args := Arguments{
		ProfilePath:        *profileArg,
		Fullscreen:         *fullscreenArg,
		RunOsmcTest:        *osmcTestArg,
		OsmcPath:           *osmcPathArg,
		DeveloperMode:      *developerModeArg,
		ShowProfileChooser: *chooserArg,
		HideMousePointer:   *hideMousePointerArg,
		ShowVersion:        *showVersionArg,
	}

	return args, true
}

func main() {
	args, ok := parseArgs()
	if !ok {
		return
	}

	if args.ShowVersion {
		ver, _ := strings.CutSuffix(Version, "\n")
		fmt.Println("PiCave", ver)
		return
	}

	if args.RunOsmcTest {
		osmc.RunTest(args.OsmcPath)
		return
	}

	app := &Application{}
	app.Application = gtk.NewApplication("com.github.nsw42.picave", gio.ApplicationFlagsNone)
	app.Arguments = args
	app.ConnectActivate(func() { app.OnActivate() })
	app.Run([]string{})
}

func (app *Application) OnActivate() {
	if app.Arguments.ShowProfileChooser {
		app.RunProfileChooser()
	} else {
		app.showMainWindow(app.Arguments.ProfilePath)
	}
}

func (app *Application) RunProfileChooser() {
	chooser := profilechooser.NewProfileChooserWindow(app.Application,
		app.Arguments.ProfilePath,
		func(profilePath string) {
			app.showMainWindow(profilePath)
		})
	chooser.Show()
}

func (app *Application) showMainWindow(profilePath string) {
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
	appWindow = appwindow.NewAppWindow(app.Application,
		prf,
		app.Arguments.Fullscreen,
		app.Arguments.DeveloperMode,
		app.Arguments.HideMousePointer,
		app.RunProfileChooser)
	appWindow.Show()
}
