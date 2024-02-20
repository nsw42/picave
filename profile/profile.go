package profile

import (
	"context"
	_ "embed"
	"encoding/json"
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

func init() {
	schema = jsonschema.Must(schemaString)
}

type Profile struct {
	FilePath            string
	VideoCacheDirectory string
	WarmUpMusic         *musicdir.MusicDirectory
	Executables         map[string]string                 // map from player name to file path
	FiletypePlayers     map[string]*FiletypePlayerOptions // map from suffix (".mp3") to player name ("mpv") and associated options
	Favourites          []string
	ShowFavouritesOnly  bool
	PowerLevels         map[string]PowerLevels // map from video id (incl DefaultVideoId) to power levels
}

type Margins struct {
	Left   int
	Right  int
	Top    int
	Bottom int
}

type FiletypePlayerOptions struct {
	Name    string
	Options []string
	Margins Margins
}

// Power level types and constants

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
	DefaultVideoId = "default"
)

// Profile file JSON keys
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

func loadProfileExecutables(configMap map[string]any) map[string]string {
	rtn := map[string]string{}
	executables := schema.JSONProp("properties").(*jsonschema.Properties).JSONProp("executables").(*jsonschema.Schema)
	executablesMap := executables.JSONProp("properties").(*jsonschema.Properties).JSONChildren()
	executableNames := maps.Keys(executablesMap)
	for _, exe := range executableNames {
		if exe[0] != '$' {
			rtn[exe] = ""
		}
	}
	if configMap[fileKeyExecutables] != nil {
		for exe, exeMap := range configMap[fileKeyExecutables].(map[string]interface{}) {
			exeMapVal := exeMap.(map[string]interface{})
			rtn[exe] = exeMapVal[fileKeyExePath].(string)
		}
	}
	return rtn
}

func loadProfileFiletypePlayers(configMap map[string]any) map[string]*FiletypePlayerOptions {
	rtn := map[string]*FiletypePlayerOptions{}
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
	profile.FiletypePlayers = loadProfileFiletypePlayers(configMap)
	profile.Favourites = stringList(configMap[fileKeyFavourites])
	profile.ShowFavouritesOnly = optionalBool(configMap[fileKeyShowFavouritesOnly])
	profile.PowerLevels = loadProfilePowerLevels(configMap)

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
	for ext, playerOpts := range profile.FiletypePlayers {
		filetypeMap[ext] = func() interface{} {
			oneFiletypeMap := map[string]any{}
			oneFiletypeMap[fileKeyPlayer] = playerOpts.Name
			oneFiletypeMap[fileKeyOptions] = playerOpts.Options
			paramMap := map[string]int{}
			if playerOpts.Margins.Left != 0 {
				paramMap[fileKeyParamMarginLeft] = playerOpts.Margins.Left
			}
			if playerOpts.Margins.Right != 0 {
				paramMap[fileKeyParamMarginRight] = playerOpts.Margins.Right
			}
			if playerOpts.Margins.Top != 0 {
				paramMap[fileKeyParamMarginTop] = playerOpts.Margins.Top
			}
			if playerOpts.Margins.Bottom != 0 {
				paramMap[fileKeyParamMarginBottom] = playerOpts.Margins.Bottom
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

func (profile *Profile) DefaultFTPVal() int {
	return profile.GetVideoFTPVal(DefaultVideoId, false)
}

func (profile *Profile) SetDefaultFTPVal(ftp int) {
	// stupid language
	powerLevel := profile.PowerLevels[DefaultVideoId]
	powerLevel.FTP = ftp
	profile.PowerLevels[DefaultVideoId] = powerLevel
}

func (profile *Profile) GetVideoFTP(videoId string, expandDefault bool) string {
	val := profile.GetVideoFTPVal(videoId, expandDefault)
	if val == 0 {
		return ""
	}
	return strconv.Itoa(val)
}

func (profile *Profile) GetVideoFTPVal(videoId string, expandDefault bool) int {
	val, found := profile.PowerLevels[videoId]
	if found && val.FTP != 0 {
		return val.FTP
	}
	if expandDefault {
		return profile.DefaultFTPVal()
	}
	return 0
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
	if expandDefault {
		return profile.GetVideoMax(DefaultVideoId, false)
	}
	return ""
}

func (profile *Profile) GetVideoMaxVal(videoId string, expandDefault bool) int {
	val, found := profile.PowerLevels[videoId]
	if found {
		max := val.Max
		switch max.ValueType {
		case NoValue:
			return 0
		case AbsoluteValue:
			return max.Absolute
		case RelativeToFTPValue:
			ftp := profile.GetVideoFTPVal(videoId, expandDefault)
			return ftp * max.PercentFTP / 100.0
		}
	}
	if expandDefault {
		return profile.GetVideoMaxVal(DefaultVideoId, false)
	}
	return 0
}

func (profile *Profile) ToggleVideoFavourite(videoId string) {
	index := slices.Index(profile.Favourites, videoId)
	if index == -1 {
		profile.Favourites = append(profile.Favourites, videoId)
	} else {
		profile.Favourites = slices.Delete(profile.Favourites, index, index+1)
	}
}

func validateProfileFile(configMap interface{}) error {
	validationState := schema.Validate(context.Background(), configMap)
	errs := *validationState.Errs
	if len(errs) > 0 {
		return fmt.Errorf(errs[0].Error())
	}

	return nil
}
