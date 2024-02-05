package feed

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

func (durn *Duration) UnmarshalJSON(bytes []byte) error {
	str := string(bytes)
	if !strings.HasPrefix(str, "\"") || !strings.HasSuffix(str, "\"") {
		return fmt.Errorf("invalid string format for duration: %s", str)
	}
	str = str[1 : len(str)-1]
	str = strings.Replace(str, " ", "", -1)
	tmp, err := time.ParseDuration(str)
	if err != nil {
		return err
	}
	*durn = Duration{tmp}
	return nil
}

func (col *Color) UnmarshalJSON(bytes []byte) error {
	var unmarshalled interface{}
	err := json.Unmarshal(bytes, &unmarshalled)
	if err != nil {
		return err
	}

	stringVal, ok := unmarshalled.(string)
	if ok {
		*col, ok = colourNames[stringVal]
		if !ok {
			return fmt.Errorf("unrecognised colour name: %s", stringVal)
		}
		return nil
	}

	arrayVal, ok := unmarshalled.([]any)
	if !ok || len(arrayVal) != 3 {
		return fmt.Errorf("unrecognised colour definition: " + string(bytes))
	}
	col.Red = int(arrayVal[0].(float64))
	col.Green = int(arrayVal[1].(float64))
	col.Blue = int(arrayVal[2].(float64))

	return nil
}

func initSessionDefinitions() {
	// initIndex and initColourNames must have been called before this

	Sessions = map[string][]SessionDefinition{}

	// Read the session definitions
	for _, videoItem := range Index {
		sessionData, err := content.ReadFile(videoItem.Id + ".json")
		if err != nil {
			panic("Unable to read session " + videoItem.Id + ".json")
		}
		var session []SessionDefinition
		if err = json.Unmarshal(sessionData, &session); err != nil {
			panic("Unable to unmarshal session " + videoItem.Id + ".json" + ": " + err.Error())
		}
		Sessions[videoItem.Id] = session
	}
}
