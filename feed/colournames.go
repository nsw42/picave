package feed

import (
	_ "embed"
	"strconv"
	"strings"
)

//go:embed rgb.txt
var rgbText string

var colourNames map[string]Color

func split(s string, sep string) []string {
	for strings.HasPrefix(s, sep) {
		s = s[len(sep):]
	}
	for strings.HasSuffix(s, sep) {
		s = s[0 : len(s)-len(sep)]
	}
	for strings.Count(s, sep+sep) > 0 {
		s = strings.Replace(s, sep+sep, sep, 1)
	}
	return strings.Split(s, sep)
}

func atof(s string) float64 {
	v, err := strconv.ParseFloat(s, 64)
	if err != nil {
		panic(err.Error())
	}
	return v
}

func initColourNames() {
	colourNames = map[string]Color{}
	lines := strings.Split(rgbText, "\n")
	for _, line := range lines {
		if line == "" {
			continue
		}
		rgbColName := split(line, "\t")
		if len(rgbColName) != 2 {
			panic("Unexpected content in line: " + line)
		}
		rgbStr := rgbColName[0]
		colName := rgbColName[1]
		rgb := split(rgbStr, " ")
		if len(rgb) != 3 {
			panic("Unexpected colour definition in line: " + line + " - len(rgb)=" + strconv.Itoa(len(rgb)))
		}
		colourNames[colName] = Color{
			Red:   atof(rgb[0]) / 255.0,
			Green: atof(rgb[1]) / 255.0,
			Blue:  atof(rgb[2]) / 255.0,
		}
	}
}
