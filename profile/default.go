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
	rtn[".mp3"] = defaultMusicPlayer(executables)
	rtn[".mk4"] = defaultVideoPlayer(executables)
	rtn[".mkv"] = defaultVideoPlayer(executables)
	return rtn
}

func defaultMusicPlayer(executables map[string]*Executable) *FiletypePlayerOptions {
	// TODO: It would be nice to generalise this - but attempting to reference players.MusicPlayerLookup results in an import cycle
	return tryFindExe(executables, "mpg123")
}

func defaultVideoPlayer(executables map[string]*Executable) *FiletypePlayerOptions {
	// omxplayer first, because that's the one that's got hardware support on the RPi
	// TODO: It would be nice to generalise this - but attempting to reference players.MusicPlayerLookup results in an import cycle
	player := tryFindExe(executables, "omxplayer")
	if player == nil {
		player = tryFindExe(executables, "mplayer")
	}
	if player == nil {
		player = tryFindExe(executables, "mpv")
	}
	return player
}

func tryFindExe(executables map[string]*Executable, exename string) *FiletypePlayerOptions {
	exe := executables[exename]
	if exe.ExePath() != "" {
		return &FiletypePlayerOptions{exename, []string{}, Margins{}}
	}
	return nil
}
