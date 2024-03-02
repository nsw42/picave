package osmc

import (
	"fmt"
	"log"
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

func NewOsmcRemoteControlReader(filepath string) Osmc {
	//
	debounced, err := NewDebouncedOsmcRemoteControlReader(filepath)
	if err != nil {
		log.Println("OSMC unavailable:", err)
		return &NullOsmcReader{}
	}
	return debounced
}

func RunTest(filepath string) {
	// An alternative to main(), which repeatedly polls for input events
	osmc := NewOsmcRemoteControlReader(filepath)
	fmt.Println("Polling for events")
	for {
		event := osmc.Poll()
		if event != nil {
			fmt.Println("Event:", event.Time, event.KeyCode, event.Pressed)
		}
	}
}
