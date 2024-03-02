package osmc

// A dummy OSMC reader, which never returns any events: used when an OSMC is not available
type NullOsmcReader struct {
}

func (*NullOsmcReader) Poll() *OsmcEvent {
	return nil
}
