package feed

import (
	"embed"
	"time"
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

type Color struct {
	Red   int
	Green int
	Blue  int
}

type Duration struct {
	time.Duration
}

type SessionDefinition struct {
	Name     string
	Type     string
	Cadence  int
	Effort   string
	Duration Duration
	Color    Color
}

var Index []VideoFeedItem
var Sessions map[string][]SessionDefinition

func init() {
	initIndex()
	initColourNames()
	initSessionDefinitions()
}
