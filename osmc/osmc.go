package osmc

import (
	"fmt"
	"time"
)

const (
	KeyBack      = 158
	KeyStop      = 128
	KeyPlayPause = 164
)

type OsmcEvent struct {
	Time    time.Time
	KeyCode uint
	Pressed bool
}

type Osmc interface {
	Poll() *OsmcEvent
}

func RunTest(filepath string, debounce bool) {
	// An alternative to main(), which repeatedly polls for input events
	var osmc Osmc
	var err error
	if debounce {
		osmc, err = NewDebouncedOsmcRemoteControlReader(filepath)
	} else {
		osmc, err = NewOsmcRemoteControlReader(filepath)
	}
	if err != nil {
		fmt.Println("Unable to open OSMC: ", err)
		return
	}
	for {
		event := osmc.Poll()
		if event != nil {
			fmt.Println("Event:", event.Time, event.KeyCode, event.Pressed)
		}
	}
}
