package profile

func DefaultProfile(filepath string) *Profile {
	profile := &Profile{}
	profile.FilePath = filepath
	profile.Executables = map[string]string{}
	profile.FiletypePlayers = map[string]*FiletypePlayerOptions{}
	profile.Favourites = []string{}
	profile.ShowFavouritesOnly = false
	profile.PowerLevels = map[string]PowerLevels{}
	profile.SetDefaultFTPVal(200)
	return profile
}
