package osmc

import (
	"bytes"
	"encoding/binary"
	"log"
	"os"
	"syscall"
	"time"
	"unsafe"
)

type OsmcRemoteControl struct {
	Handle *os.File
}

type InputEventData struct {
	Seconds      uintNative // If you get compile errors about an unknown type uintNative, update native32.go or native64.go
	Microseconds uintNative // ... to ensure your platform is represented, and the appropriate type alias is defined
	Type         uint16
	Code         uint16
	Value        uint32
}

const (
	EventSize = int(unsafe.Sizeof(InputEventData{}))

	EventKeyType = 1
)

func NewOsmcRemoteControlReader(filename string) (*OsmcRemoteControl, error) {
	if filename == "" {
		filename = "/dev/input/by-id/usb-OSMC_Remote_Controller_USB_Keyboard_Mouse-event-if01"
	}
	handle, err := os.OpenFile(filename, syscall.O_RDONLY|syscall.O_NDELAY, 0444)
	if err != nil || handle == nil {
		return nil, err
	}
	return &OsmcRemoteControl{handle}, nil
}

func (osmc *OsmcRemoteControl) Poll() *OsmcEvent {
	// Linux document states that we'll always get an integer number of input events on a read.
	// So, no need for the accumulator that was implemented in the original Python version.
	tmpBuf := make([]byte, EventSize)
	n, err := osmc.Handle.Read(tmpBuf)
	if err != nil {
		log.Println("Error reading from osmc file", err)
		return nil
	}
	if n == 0 {
		return nil
	}
	reader := bytes.NewReader(tmpBuf)
	var inputEvent InputEventData
	err = binary.Read(reader, binary.LittleEndian, &inputEvent)
	if err != nil {
		log.Println("binary.Read failed:", err)
		return nil
	}
	// fmt.Println("Decoded bytes: sec:", inputEvent.Seconds, "usec:", inputEvent.Microseconds, "type", inputEvent.Type, "code", inputEvent.Code, "value", inputEvent.Value)
	if inputEvent.Type != EventKeyType {
		// This log println can be useful if the decoding of the input event isn't working as expected
		// but it's normal to see other events with the OSMC - e.g. it sends
		// EV_MSC (4) / MSC_SCAN (4) - which are no use to use.
		// log.Println("Got unexpected key event type: Expected ", EventKeyType, "got", inputEvent.Type)
		return nil
	}
	osmcEvent := OsmcEvent{
		time.Unix(int64(inputEvent.Seconds), int64(inputEvent.Microseconds)*1000),
		uint(inputEvent.Code),
		inputEvent.Value != 0,
	}
	return &osmcEvent
}
