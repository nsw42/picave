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

type Profile struct {
	VideoCacheDirectory   string
	WarmUpMusic           musicdir.MusicDirectory
	Executables           map[string]string // map from player
	FiletypePlayers       map[string]string // map from suffix (".mp3") to player name ("mpv")
	FiletypePlayerOptions map[string]FiletypePlayerOptions
	Favourites            []string
	ShowFavouritesOnly    bool
	PowerLevels           map[string]PowerLevels
}

type FiletypePlayerOptions struct {
	Options      []string
	MarginLeft   int
	MarginRight  int
	MarginTop    int
	MarginBottom int
}

type PowerLevels struct {
	Max MaxPowerLevel
	FTP int
}

type MaxPowerLevel struct {
	ValueType  PowerLevelType
	Absolute   int
	PercentFTP int
}

type PowerLevelType int

const (
	NoValue PowerLevelType = iota
	AbsoluteValue
	RelativeToFTPValue
)

func maxPowerLevel(val interface{}) MaxPowerLevel {
	if val == nil {
		return MaxPowerLevel{ValueType: NoValue}
	}
	switch value := val.(type) {
	default:
		return MaxPowerLevel{ValueType: NoValue}
	case float64:
		return MaxPowerLevel{ValueType: AbsoluteValue, Absolute: int(value)}
	case string:
		if strings.HasSuffix(value, "%") {
			intVal, _ := strconv.ParseInt(strings.TrimRight(value, "%"), 10, 64)
			return MaxPowerLevel{ValueType: RelativeToFTPValue, PercentFTP: int(intVal)}
		} else {
			floatVal, _ := strconv.ParseFloat(value, 64)
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
	configMap := map[string]any{}
	decoder.Decode(&configMap)

	if err := validateProfileFile(configMap); err != nil {
		return nil, err
	}

	profile := &Profile{}
	profile.VideoCacheDirectory = configMap["video_cache_directory"].(string)
	warmUpMusicDirectory := optionalString(configMap["warm_up_music_directory"])
	if warmUpMusicDirectory != "" {
		profile.WarmUpMusic = musicdir.FindMusicFiles(warmUpMusicDirectory)
	}
	profile.Executables = map[string]string{}
	if configMap["executables"] != nil {
		for exe, exeMap := range configMap["executables"].(map[string]interface{}) {
			exeMapVal := exeMap.(map[string]interface{})
			profile.Executables[exe] = exeMapVal["path"].(string)
		}
	}
	profile.FiletypePlayers = map[string]string{}
	profile.FiletypePlayerOptions = map[string]FiletypePlayerOptions{}
	if configMap["filetypes"] != nil {
		for filetype, playerMap := range configMap["filetypes"].(map[string]interface{}) {
			playerMapVal := playerMap.(map[string]interface{})
			options := FiletypePlayerOptions{}
			playerName := playerMapVal["player"].(string)
			// TODO: The easy way of checking whether this is a known player results in an import cycle.
			// Fix this another day
			// if _, ok := players.PlayerLookup[playerName]; !ok {
			// 	fmt.Println("Unrecognised player ", playerName, " selected for filetype ", filetype)
			// 	continue
			// }
			profile.FiletypePlayers[filetype] = playerName
			options.Options = stringList(playerMapVal["options"])

			if playerMapVal["parameters"] != nil {
				paramsMap := playerMapVal["parameters"].(map[string]interface{})
				options.MarginLeft = optionalInt(paramsMap["margin_left"])
				options.MarginRight = optionalInt(paramsMap["margin_right"])
				options.MarginTop = optionalInt(paramsMap["margin_top"])
				options.MarginBottom = optionalInt(paramsMap["margin_bottom"])
			}
			profile.FiletypePlayerOptions[filetype] = options
		}
	}
	profile.Favourites = stringList(configMap["favourites"])
	profile.ShowFavouritesOnly = optionalBool(configMap["show_favourites_only"])
	profile.PowerLevels = map[string]PowerLevels{}
	if configMap["power_levels"] != nil {
		for video, videoPowerLevelsMap := range configMap["power_levels"].(map[string]interface{}) {
			videoPowerLevelsMapVal := videoPowerLevelsMap.(map[string]interface{})
			levels := PowerLevels{}
			levels.FTP = optionalInt(videoPowerLevelsMapVal["FTP"])
			levels.Max = maxPowerLevel(videoPowerLevelsMapVal["MAX"])
			profile.PowerLevels[video] = levels
		}
	}

	return profile, nil
}

func (profile *Profile) GetVideoFTP(videoId string, expandDefault bool) string {
	val, found := profile.PowerLevels[videoId]
	if found && val.FTP != 0 {
		return strconv.Itoa(val.FTP)
	}
	return ""
}

func (profile *Profile) GetVideoMax(videoId string, expandDefault bool) string {
	val, found := profile.PowerLevels[videoId]
	if found {
		max := val.Max
		switch max.ValueType {
		case NoValue:
			return ""
		case AbsoluteValue:
			return strconv.Itoa(max.Absolute)
		case RelativeToFTPValue:
			return fmt.Sprintf("%d%%", max.PercentFTP)
		}
	}
	return ""
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
