package profile

func DefaultProfile(filepath string) *Profile {
	profile := &Profile{}
	profile.FilePath = filepath
	profile.Executables = defaultProfileExecutables()
	profile.FiletypePlayers = defaultProfilePlayers(profile.Executables)
	profile.Favourites = []string{}
	profile.ShowFavouritesOnly = false
	profile.PowerLevels = map[string]PowerLevels{}
	profile.SetDefaultFTPVal(200)
	return profile
}

func defaultProfileExecutables() map[string]*Executable {
	rtn := map[string]*Executable{}
	for _, exe := range executableNames {
		rtn[exe] = NewExecutable(exe, "")
	}
	return rtn
}

func defaultProfilePlayers(executables map[string]*Executable) map[string]*FiletypePlayerOptions {
	rtn := map[string]*FiletypePlayerOptions{}
	for _, filetype := range supportedFiletypes {
		rtn[filetype] = nil
	}
	rtn[".mp3"] = defaultMusicPlayer(executables)
	return rtn
}

func defaultMusicPlayer(executables map[string]*Executable) *FiletypePlayerOptions {
	// TODO: It would be nice to generalise this - but attempting to reference players.MusicPlayerLookup results in an import cycle
	mpg123 := executables["mpg123"]
	if mpg123.ExePath() != "" {
		return &FiletypePlayerOptions{"mpg123", []string{}, Margins{}}
	}
	return nil
}
