package profile

import (
	"context"
	_ "embed"
	"fmt"
	"nsw42/picave/musicdir"
	"os"
	"strconv"
	"strings"

	"github.com/qri-io/jsonschema"
	"github.com/titanous/json5"
)

//go:embed profile.schema.json
var schemaString string

type FiletypePlayerOptions struct {
	Player       string
	Options      []string
	MarginLeft   int
	MarginRight  int
	MarginTop    int
	MarginBottom int
}

type PowerLevelType int

const (
	NoValue PowerLevelType = iota
	AbsoluteValue
	RelovateToFTPValue
)

type MaxPowerLevel struct {
	ValueType   PowerLevelType
	Absolute    int
	MultipleFTP float64
}

type PowerLevels struct {
	Max MaxPowerLevel
	FTP int
}

type Profile struct {
	VideoCacheDirectory string
	WarmUpMusic         musicdir.MusicDirectory
	Executables         map[string]string
	FiletypePlayers     map[string]FiletypePlayerOptions
	Favourites          []string
	ShowFavouritesOnly  bool
	PowerLevels         map[string]PowerLevels
}

func maxPowerLevel(val interface{}) MaxPowerLevel {
	if val == nil {
		return MaxPowerLevel{ValueType: NoValue}
	}
	switch val.(type) {
	default:
		return MaxPowerLevel{ValueType: NoValue}
	case float64:
		return MaxPowerLevel{ValueType: AbsoluteValue, Absolute: int(val.(float64))}
	case string:
		stringVal := val.(string)
		if strings.HasSuffix(stringVal, "%") {
			floatVal, _ := strconv.ParseFloat(strings.TrimRight(stringVal, "%"), 64)
			return MaxPowerLevel{ValueType: RelovateToFTPValue, MultipleFTP: floatVal / 100.}
		} else {
			floatVal, _ := strconv.ParseFloat(stringVal, 64)
			return MaxPowerLevel{ValueType: AbsoluteValue, Absolute: int(floatVal)}
		}
	}
}

func optionalInt(val any) int {
	if val == nil {
		return 0
	}
	return int(val.(float64))
}

func optionalBool(val any) bool {
	if val == nil {
		return false
	}
	return val.(bool)
}

func optionalString(val any) string {
	if val == nil {
		return ""
	}
	return val.(string)
}

func stringList(jsonSlice interface{}) []string {
	rtn := []string{}
	if jsonSlice != nil {
		for _, option := range jsonSlice.([]interface{}) {
			rtn = append(rtn, option.(string))
		}
	}
	return rtn
}

func LoadProfile(profileFilePath string) (*Profile, error) {
	reader, err := os.Open(profileFilePath)
	if err != nil {
		return nil, err
	}
	defer reader.Close()

	decoder := json5.NewDecoder(reader)
	configMap := make(map[string]any, 1)
	decoder.Decode(&configMap)

	if err := validateProfileFile(configMap); err != nil {
		return nil, err
	}

	configFile := &Profile{}
	configFile.VideoCacheDirectory = configMap["video_cache_directory"].(string)
	warmUpMusicDirectory := optionalString(configMap["warm_up_music_directory"])
	if warmUpMusicDirectory != "" {
		configFile.WarmUpMusic = musicdir.FindMusicFiles(warmUpMusicDirectory)
	}
	configFile.Executables = make(map[string]string, 5)
	if configMap["executables"] != nil {
		for exe, exeMap := range configMap["executables"].(map[string]interface{}) {
			exeMapVal := exeMap.(map[string]interface{})
			configFile.Executables[exe] = exeMapVal["path"].(string)
		}
	}
	configFile.FiletypePlayers = make(map[string]FiletypePlayerOptions, 5)
	if configMap["filetypes"] != nil {
		for filetype, playerMap := range configMap["filetypes"].(map[string]interface{}) {
			playerMapVal := playerMap.(map[string]interface{})
			options := FiletypePlayerOptions{}
			options.Player = playerMapVal["player"].(string)
			options.Options = stringList(playerMapVal["options"])

			if playerMapVal["parameters"] != nil {
				paramsMap := playerMapVal["parameters"].(map[string]interface{})
				options.MarginLeft = optionalInt(paramsMap["margin_left"])
				options.MarginRight = optionalInt(paramsMap["margin_right"])
				options.MarginTop = optionalInt(paramsMap["margin_top"])
				options.MarginBottom = optionalInt(paramsMap["margin_bottom"])
			}
			configFile.FiletypePlayers[filetype] = options
		}
	}
	configFile.Favourites = stringList(configMap["favourites"])
	configFile.ShowFavouritesOnly = optionalBool(configMap["show_favourites_only"])
	configFile.PowerLevels = make(map[string]PowerLevels, 10)
	if configMap["power_levels"] != nil {
		for video, videoPowerLevelsMap := range configMap["power_levels"].(map[string]interface{}) {
			videoPowerLevelsMapVal := videoPowerLevelsMap.(map[string]interface{})
			levels := PowerLevels{}
			levels.FTP = optionalInt(videoPowerLevelsMapVal["FTP"])
			levels.Max = maxPowerLevel(videoPowerLevelsMapVal["MAX"])
			configFile.PowerLevels[video] = levels
		}
	}

	return configFile, nil
}

func validateProfileFile(configMap interface{}) error {
	schema := jsonschema.Must(schemaString)

	validationState := schema.Validate(context.Background(), configMap)
	errs := *validationState.Errs
	if len(errs) > 0 {
		return fmt.Errorf(errs[0].Error())
	}

	return nil
}
