package widgets

import "github.com/diamondburned/gotk4/pkg/gtk/v4"

func NewIntegerSpinner(lower, upper, value int) *gtk.SpinButton {
	adjustment := gtk.NewAdjustment(float64(value), float64(lower), float64(upper), 1.0, 5.0, 0.0)
	return gtk.NewSpinButton(adjustment, 1.0, 0)
}
