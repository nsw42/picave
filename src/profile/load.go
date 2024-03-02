package profile

import (
	"context"
	_ "embed"
	"fmt"
	"nsw42/picave/musicdir"
	"os"
	"slices"
	"strconv"
	"strings"

	"github.com/qri-io/jsonschema"
	"github.com/titanous/json5"
	"golang.org/x/exp/maps"
)

//go:embed profile.schema.json
var schemaString string
var schema *jsonschema.Schema
var executableNames []string
var supportedFiletypes []string

func init() {
	schema = jsonschema.Must(schemaString)
	schemaProperties := schema.JSONProp("properties").(*jsonschema.Properties)
	executables := schemaProperties.JSONProp(fileKeyExecutables).(*jsonschema.Schema)
	executablesMap := executables.JSONProp("properties").(*jsonschema.Properties).JSONChildren()
	executableNames = maps.Keys(executablesMap)
	executableNames = slices.DeleteFunc[[]string](executableNames, func(s string) bool {
		return s == "" || s[0] == '$'
	})
	filetypes := schemaProperties.JSONProp(fileKeyFiletypes).(*jsonschema.Schema)
	filetypesMap := filetypes.JSONProp("properties").(*jsonschema.Properties).JSONChildren()
	supportedFiletypes = maps.Keys(filetypesMap)
}

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

func loadProfileExecutables(configMap map[string]any) map[string]*Executable {
	rtn := defaultProfileExecutables() // Ensure every executable has a value, although possibly not a useful one
	if configMap[fileKeyExecutables] != nil {
		for exe, exeMap := range configMap[fileKeyExecutables].(map[string]interface{}) {
			exeMapVal := exeMap.(map[string]interface{})
			rtn[exe] = NewExecutable(exe, exeMapVal[fileKeyExePath].(string))
		}
	}
	return rtn
}

func loadProfileFiletypePlayers(executables map[string]*Executable, configMap map[string]any) map[string]*FiletypePlayerOptions {
	rtn := defaultProfilePlayers(executables) // Ensure every player has a value, although possibly not a useful one
	if configMap[fileKeyFiletypes] != nil {
		for filetype, playerMap := range configMap[fileKeyFiletypes].(map[string]interface{}) {
			playerMapVal := playerMap.(map[string]interface{})
			options := FiletypePlayerOptions{}
			playerName := playerMapVal[fileKeyPlayer].(string)
			// The easy way of checking whether this is a known player (checking in players.FooPlayerLookup)
			// results in an import cycle. So, instead, just rely on the schema matching the implementation.
			options.Name = playerName
			options.Options = stringList(playerMapVal[fileKeyOptions])

			if playerMapVal[fileKeyParameters] != nil {
				paramsMap := playerMapVal[fileKeyParameters].(map[string]interface{})
				options.Margins.Left = optionalInt(paramsMap[fileKeyParamMarginLeft])
				options.Margins.Right = optionalInt(paramsMap[fileKeyParamMarginRight])
				options.Margins.Top = optionalInt(paramsMap[fileKeyParamMarginTop])
				options.Margins.Bottom = optionalInt(paramsMap[fileKeyParamMarginBottom])
			}
			rtn[filetype] = &options
		}
	}
	return rtn
}

func loadProfilePowerLevels(configMap map[string]any) map[string]PowerLevels {
	rtn := map[string]PowerLevels{}
	if configMap[fileKeyPowerLevels] != nil {
		for video, videoPowerLevelsMap := range configMap[fileKeyPowerLevels].(map[string]interface{}) {
			videoPowerLevelsMapVal := videoPowerLevelsMap.(map[string]interface{})
			levels := PowerLevels{}
			levels.FTP = optionalInt(videoPowerLevelsMapVal[fileKeyFTP])
			levels.Max = maxPowerLevel(videoPowerLevelsMapVal[fileKeyMax])
			rtn[video] = levels
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
	profile.FilePath = profileFilePath
	profile.VideoCacheDirectory = configMap[fileKeyVideoCacheDirectory].(string)
	warmUpMusicDirectory := optionalString(configMap[fileKeyWarmUpMusicDirectory])
	if warmUpMusicDirectory != "" {
		profile.WarmUpMusic = musicdir.NewMusicDirectory(warmUpMusicDirectory)
	}
	profile.Executables = loadProfileExecutables(configMap)
	profile.FiletypePlayers = loadProfileFiletypePlayers(profile.Executables, configMap)
	profile.Favourites = stringList(configMap[fileKeyFavourites])
	profile.ShowFavouritesOnly = optionalBool(configMap[fileKeyShowFavouritesOnly])
	profile.PowerLevels = loadProfilePowerLevels(configMap)

	return profile, nil
}

func validateProfileFile(configMap interface{}) error {
	validationState := schema.Validate(context.Background(), configMap)
	errs := *validationState.Errs
	if len(errs) > 0 {
		return fmt.Errorf(errs[0].Error())
	}

	return nil
}
