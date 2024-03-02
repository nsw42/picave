package feed

import "encoding/json"

func initIndex() {
	// Read the index
	indexData, err := content.ReadFile("index.json")
	if err != nil {
		panic("Unable to find index.json in embedded FS: " + err.Error())
	}
	if err = json.Unmarshal(indexData, &Index); err != nil {
		panic("Unable to unmarshal index: " + err.Error())
	}
}
