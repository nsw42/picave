package utils

import (
	"fmt"
	"time"
)

func FormatDurationMMSS(durn time.Duration) string {
	mm := int(durn.Minutes())
	ss := int(durn.Seconds()) - mm*60
	return fmt.Sprintf("%02d:%02d ", mm, ss)
}
