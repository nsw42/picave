package profile

func DefaultProfile(filepath string) *Profile {
	profile := &Profile{}
	profile.FilePath = filepath
	profile.Executables = defaultProfileExecutables()
	profile.FiletypePlayers = map[string]*FiletypePlayerOptions{}
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
