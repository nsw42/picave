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
	Red   float64
	Green float64
	Blue  float64
}

// These are similar to profile.PowerLevel, but different
type IntervalPowerLevel struct {
	Type       IntervalPowerLevelType
	PercentFTP int
}

type IntervalPowerLevelType int

const (
	RelativeToFTPValue IntervalPowerLevelType = iota
	MaxEffort
)

type Duration struct {
	time.Duration
}

type IntervalDefinition struct {
	Name     string
	Type     string
	Cadence  int
	Effort   IntervalPowerLevel
	Duration Duration
	Color    Color
}

type SessionDefinition struct {
	VideoId   string
	Intervals []IntervalDefinition
}

var Index []VideoFeedItem
var Sessions map[string]*SessionDefinition

func init() {
	initIndex()
	initColourNames()
	initSessionDefinitions()
}
