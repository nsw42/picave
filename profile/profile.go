package profile

import (
	"context"
	_ "embed"
	"encoding/json"
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
	FilePath              string
	VideoCacheDirectory   string
	WarmUpMusic           *musicdir.MusicDirectory
	Executables           map[string]string // map from player name to file path
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

const (
	fileKeyVideoCacheDirectory  = "video_cache_directory"
	fileKeyWarmUpMusicDirectory = "warm_up_music_directory"
	fileKeyExecutables          = "executables"
	fileKeyExePath              = "path"
	fileKeyFiletypes            = "filetypes"
	fileKeyPlayer               = "player"
	fileKeyOptions              = "options"
	fileKeyParameters           = "parameters"
	fileKeyParamMarginLeft      = "margin_left"
	fileKeyParamMarginRight     = "margin_right"
	fileKeyParamMarginTop       = "margin_top"
	fileKeyParamMarginBottom    = "margin_bottom"
	fileKeyFavourites           = "favourites"
	fileKeyShowFavouritesOnly   = "show_favourites_only"
	fileKeyPowerLevels          = "power_levels"
	fileKeyFTP                  = "FTP"
	fileKeyMax                  = "MAX"
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
	profile.FilePath = profileFilePath
	profile.VideoCacheDirectory = configMap[fileKeyVideoCacheDirectory].(string)
	warmUpMusicDirectory := optionalString(configMap[fileKeyWarmUpMusicDirectory])
	if warmUpMusicDirectory != "" {
		profile.WarmUpMusic = musicdir.FindMusicFiles(warmUpMusicDirectory)
	}
	profile.Executables = map[string]string{}
	if configMap[fileKeyExecutables] != nil {
		for exe, exeMap := range configMap[fileKeyExecutables].(map[string]interface{}) {
			exeMapVal := exeMap.(map[string]interface{})
			profile.Executables[exe] = exeMapVal[fileKeyExePath].(string)
		}
	}
	profile.FiletypePlayers = map[string]string{}
	profile.FiletypePlayerOptions = map[string]FiletypePlayerOptions{}
	if configMap[fileKeyFiletypes] != nil {
		for filetype, playerMap := range configMap[fileKeyFiletypes].(map[string]interface{}) {
			playerMapVal := playerMap.(map[string]interface{})
			options := FiletypePlayerOptions{}
			playerName := playerMapVal[fileKeyPlayer].(string)
			// TODO: The easy way of checking whether this is a known player results in an import cycle.
			// Fix this another day
			// if _, ok := players.PlayerLookup[playerName]; !ok {
			// 	fmt.Println("Unrecognised player ", playerName, " selected for filetype ", filetype)
			// 	continue
			// }
			profile.FiletypePlayers[filetype] = playerName
			options.Options = stringList(playerMapVal[fileKeyOptions])

			if playerMapVal[fileKeyParameters] != nil {
				paramsMap := playerMapVal[fileKeyParameters].(map[string]interface{})
				options.MarginLeft = optionalInt(paramsMap[fileKeyParamMarginLeft])
				options.MarginRight = optionalInt(paramsMap[fileKeyParamMarginRight])
				options.MarginTop = optionalInt(paramsMap[fileKeyParamMarginTop])
				options.MarginBottom = optionalInt(paramsMap[fileKeyParamMarginBottom])
			}
			profile.FiletypePlayerOptions[filetype] = options
		}
	}
	profile.Favourites = stringList(configMap[fileKeyFavourites])
	profile.ShowFavouritesOnly = optionalBool(configMap[fileKeyShowFavouritesOnly])
	profile.PowerLevels = map[string]PowerLevels{}
	if configMap[fileKeyPowerLevels] != nil {
		for video, videoPowerLevelsMap := range configMap[fileKeyPowerLevels].(map[string]interface{}) {
			videoPowerLevelsMapVal := videoPowerLevelsMap.(map[string]interface{})
			levels := PowerLevels{}
			levels.FTP = optionalInt(videoPowerLevelsMapVal[fileKeyFTP])
			levels.Max = maxPowerLevel(videoPowerLevelsMapVal[fileKeyMax])
			profile.PowerLevels[video] = levels
		}
	}

	return profile, nil
}

func (profile *Profile) buildExecutablesJsonModel() interface{} {
	exeMap := map[string]map[string]string{}
	for playerName, filePath := range profile.Executables {
		exeMap[playerName] = map[string]string{fileKeyExePath: filePath}
	}
	return exeMap
}

func (profile *Profile) buildFiletypesJsonModel() interface{} {
	filetypeMap := map[string]any{}
	for ext, playerName := range profile.FiletypePlayers {
		filetypeMap[ext] = func() interface{} {
			oneFiletypeMap := map[string]any{}
			oneFiletypeMap[fileKeyPlayer] = playerName
			opts := profile.FiletypePlayerOptions[ext]
			oneFiletypeMap[fileKeyOptions] = opts.Options
			paramMap := map[string]int{}
			if opts.MarginLeft != 0 {
				paramMap[fileKeyParamMarginLeft] = opts.MarginLeft
			}
			if opts.MarginRight != 0 {
				paramMap[fileKeyParamMarginRight] = opts.MarginRight
			}
			if opts.MarginTop != 0 {
				paramMap[fileKeyParamMarginTop] = opts.MarginTop
			}
			if opts.MarginBottom != 0 {
				paramMap[fileKeyParamMarginBottom] = opts.MarginBottom
			}
			oneFiletypeMap[fileKeyParameters] = paramMap
			return oneFiletypeMap
		}()
	}
	return filetypeMap
}

func (profile *Profile) buildPowerLevelsJsonModel() interface{} {
	powerLevelMap := map[string]any{}
	for videoId, powerLevels := range profile.PowerLevels {
		powerLevelMap[videoId] = func() map[string]interface{} {
			onePowerLevelMap := map[string]any{}
			if powerLevels.FTP != 0 {
				onePowerLevelMap[fileKeyFTP] = powerLevels.FTP
			}
			switch powerLevels.Max.ValueType {
			case NoValue:
				break
			case AbsoluteValue:
				onePowerLevelMap[fileKeyMax] = powerLevels.Max.Absolute
			case RelativeToFTPValue:
				onePowerLevelMap[fileKeyMax] = fmt.Sprintf("%d%%", powerLevels.Max.PercentFTP)
			}
			return onePowerLevelMap
		}()
	}
	return powerLevelMap
}

func (profile *Profile) Save() error {
	toWrite := map[string]any{}
	toWrite[fileKeyVideoCacheDirectory] = profile.VideoCacheDirectory
	if profile.WarmUpMusic != nil {
		toWrite[fileKeyWarmUpMusicDirectory] = profile.WarmUpMusic.BasePath
	}
	toWrite[fileKeyExecutables] = profile.buildExecutablesJsonModel()
	toWrite[fileKeyFiletypes] = profile.buildFiletypesJsonModel()
	toWrite[fileKeyFavourites] = profile.Favourites
	toWrite[fileKeyShowFavouritesOnly] = profile.ShowFavouritesOnly
	toWrite[fileKeyPowerLevels] = profile.buildPowerLevelsJsonModel()
	formatted, err := json.MarshalIndent(toWrite, "", "    ")
	if err != nil {
		return err
	}
	os.WriteFile(profile.FilePath, formatted, 0666)

	return nil
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
