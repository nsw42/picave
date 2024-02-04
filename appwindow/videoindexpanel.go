package appwindow

import (
	"nsw42/picave/feed"
	"slices"

	"github.com/diamondburned/gotk4/pkg/gdk/v4"
	"github.com/diamondburned/gotk4/pkg/glib/v2"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type VideoIndexPanel struct {
	Parent    *AppWindow
	Contents  *gtk.Grid
	ListStore *gtk.ListStore
	TreeView  *gtk.TreeView
}

type ListStoreColumn int

const (
	ColumnFavourite = iota
	ColumnTitle     = iota
	ColumnType
	ColumnDuration
	ColumnDate
	ColumnEffectiveFTP
	ColumnEffectiveMax
	// ColumnVideoDownloaded
	ColumnVideoId
	ColumnShowRow
)

var favouriteIcon string // *gdkpixbuf.Pixbuf

func loadIcon(iconsToTry []string) string {
	display := gdk.DisplayGetDefault()
	if display == nil {
		panic("No display")
	}
	theme := gtk.IconThemeGetForDisplay(display)
	if theme == nil {
		panic("Unable to find theme")
	}
	icon := theme.LookupIcon(iconsToTry[0], iconsToTry[1:], 32, 1, gtk.TextDirLTR, 0)
	if icon == nil {
		panic("Unable to find icon: " + iconsToTry[0])
	}
	return icon.IconName()
	// iconPath := icon.File().Path()
	// pixbuf, err := gdkpixbuf.NewPixbufFromFile(iconPath)
	// if err != nil {
	// 	panic("Unable to load file: " + iconPath)
	// }
	// return pixbuf
}

func createColumn(title string, renderer gtk.CellRendererer, expand bool, renderAttribute string, colNr ListStoreColumn) *gtk.TreeViewColumn {
	column := gtk.NewTreeViewColumn()
	column.SetTitle(title)
	column.PackEnd(renderer, expand)
	column.AddAttribute(renderer, renderAttribute, int(colNr))
	column.SetResizable(true)
	return column
}

func createTextColumn(title string, colNr ListStoreColumn) *gtk.TreeViewColumn {
	renderer := gtk.NewCellRendererText()
	return createColumn(title, renderer, true, "text", colNr)
}

func createPixbufColumn(title string, colNr ListStoreColumn) *gtk.TreeViewColumn {
	renderer := gtk.NewCellRendererPixbuf()
	renderer.SetAlignment(0.5, 0.5)
	renderer.SetPadding(0, 4)
	return createColumn(title, renderer, false, "icon-name", colNr)
}

func NewVideoIndexPanel(parent *AppWindow) *VideoIndexPanel {
	if favouriteIcon == "" {
		favouriteIcon = loadIcon([]string{"starred-symbolic", "starred"})
	}
	rtn := &VideoIndexPanel{Parent: parent}
	rtn.ListStore = rtn.buildListStore()

	rtn.TreeView = gtk.NewTreeView()
	rtn.TreeView.AppendColumn(createPixbufColumn("Favourite", ColumnFavourite))
	rtn.TreeView.AppendColumn(createTextColumn("Title", ColumnTitle))
	rtn.TreeView.AppendColumn(createTextColumn("Type", ColumnType))
	rtn.TreeView.AppendColumn(createTextColumn("Duration", ColumnDuration))
	rtn.TreeView.AppendColumn(createTextColumn("Date", ColumnDate))
	rtn.TreeView.AppendColumn(createTextColumn("FTP", ColumnEffectiveFTP))
	rtn.TreeView.AppendColumn(createTextColumn("Max", ColumnEffectiveMax))
	rtn.TreeView.SetModel(rtn.ListStore)
	rtn.TreeView.SetEnableSearch(false)

	scrollableTree := gtk.NewScrolledWindow()
	scrollableTree.SetHExpand(true)
	scrollableTree.SetVExpand(true)
	scrollableTree.SetChild(rtn.TreeView)

	backButton := gtk.NewButtonWithLabel("Back")
	backButton.ConnectClicked(rtn.OnBackClicked)

	grid := gtk.NewGrid()
	grid.SetMarginTop(100)
	grid.SetMarginBottom(100)
	grid.SetMarginStart(200)
	grid.SetMarginEnd(200)
	grid.Attach(scrollableTree, 0, 0, 1, 3)
	grid.Attach(backButton, 0, 5, 1, 1)
	rtn.Contents = grid

	return rtn
}

func (panel *VideoIndexPanel) OnBackClicked() {
	panel.Parent.Stack.SetVisibleChildName(MainPanelName)
}

func (panel *VideoIndexPanel) buildListStore() *gtk.ListStore {
	listStore := gtk.NewListStore([]glib.Type{
		glib.TypeString, // fav
		glib.TypeString, // title
		glib.TypeString, // session type
		glib.TypeString, // video duration
		glib.TypeString, // video date
		glib.TypeString, // FTP
		glib.TypeString, // Max
		// gdkpixbuf.Pixbuf, // downloaded
		glib.TypeString,  // Video ID
		glib.TypeBoolean, // Show Row
	})
	for _, videoItem := range feed.Index {
		var favIcon string
		if slices.Contains(panel.Parent.Profile.Favourites, videoItem.Id) {
			favIcon = favouriteIcon
		}
		newRow := listStore.Append()
		listStore.Set(newRow,
			[]int{ColumnFavourite, ColumnTitle, ColumnType, ColumnDuration, ColumnDate, ColumnEffectiveFTP, ColumnEffectiveMax, ColumnVideoId, ColumnShowRow},
			[]glib.Value{*glib.NewValue(favIcon),
				*glib.NewValue(videoItem.Name),
				*glib.NewValue(videoItem.Type),
				*glib.NewValue(videoItem.Duration),
				*glib.NewValue(videoItem.Date),
				*glib.NewValue(formatPower(panel.Parent.Profile.GetVideoFTP(videoItem.Id, false))),
				*glib.NewValue(formatPower(panel.Parent.Profile.GetVideoMax(videoItem.Id, false))),
			})
	}
	return listStore
}

func formatPower(power string) string {
	if power == "" {
		return "Dflt"
	}
	return power
}
