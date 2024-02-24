package profile

import (
	"encoding/json"
	"fmt"
	"os"
)

func (profile *Profile) buildExecutablesJsonModel() interface{} {
	exeMap := map[string]map[string]string{}
	for playerName, exe := range profile.Executables {
		if exe != nil && exe.ConfiguredPath != "" {
			exeMap[playerName] = map[string]string{fileKeyExePath: exe.ConfiguredPath}
		}
	}
	return exeMap
}

func (profile *Profile) buildFiletypesJsonModel() interface{} {
	filetypeMap := map[string]any{}
	for ext, playerOpts := range profile.FiletypePlayers {
		if playerOpts != nil {
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
