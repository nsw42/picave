package feed

import (
	"embed"
	"encoding/json"
)

//go:embed *.json
var content embed.FS

type VideoFeedItem struct {
	Name     string
	Id       string
	Url      string
	Date     string
	Duration string
	Type     string
}

var Index []VideoFeedItem

func init() {
	indexData, err := content.ReadFile("index.json")
	if err != nil {
		panic("Unable to find index.json in embedded FS: " + err.Error())
	}
	if err = json.Unmarshal(indexData, &Index); err != nil {
		panic("Unable to unmarshal index: " + err.Error())
	}
}
