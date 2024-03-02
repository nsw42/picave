package osmc

const DebounceInterval = 1.0 // seconds

type DebouncedOsmcRemotecontrol struct {
	OsmcRemoteControl
	LastEvent OsmcEvent
}

func NewDebouncedOsmcRemoteControlReader(filepath string) (*DebouncedOsmcRemotecontrol, error) {
	debounced := &DebouncedOsmcRemotecontrol{}
	osmc, err := NewRawOsmcRemoteControlReader(filepath)
	if err != nil {
		return nil, err
	}
	debounced.OsmcRemoteControl = *osmc
	return debounced, nil
}

func (debounced *DebouncedOsmcRemotecontrol) Poll() *OsmcEvent {
	event := debounced.OsmcRemoteControl.Poll()
	if event == nil {
		return nil
	}
	if event.KeyCode == debounced.LastEvent.KeyCode && event.Time.Sub(debounced.LastEvent.Time).Seconds() < DebounceInterval {
		// Note that this simplistic debouncing means we never see 'key release' events.
		// This is OK for our purposes, but might prove problematic in other contexts.
		// log.Println("Debounce: ignoring event")
		return nil
	}
	debounced.LastEvent = *event
	return event
}
