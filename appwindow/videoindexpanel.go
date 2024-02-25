package appwindow

import (
	"fmt"
	"nsw42/picave/feed"
	"nsw42/picave/powerdialog"
	"nsw42/picave/widgets"
	"slices"

	"github.com/diamondburned/gotk4/pkg/gdk/v4"
	"github.com/diamondburned/gotk4/pkg/glib/v2"
	"github.com/diamondburned/gotk4/pkg/gtk/v4"
)

type VideoIndexPanel struct {
	Parent                   *AppWindow
	Contents                 *gtk.Grid
	ListStore                *gtk.ListStore
	ListStoreRows            []*gtk.TreeIter
	ListStoreFavouriteFilter *gtk.TreeModelFilter
	TreeView                 *gtk.TreeView
	SessionPreview           *widgets.SessionPreview
	KeyController            *gtk.EventControllerKey
	FavouriteIcon            string
	DownloadedIcon           string
	DownloadingIcon          string
	DownloadBlockedIcon      string
}

type ListStoreColumn int

const (
	ColumnFavourite = iota
	ColumnTitle
	ColumnType
	ColumnDuration
	ColumnDate
	ColumnEffectiveFTP
	ColumnEffectiveMax
	ColumnVideoDownloaded
	ColumnVideoId
	ColumnShowRow
)

func findIcon(iconsToTry []string) string {
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
	rtn := &VideoIndexPanel{Parent: parent}
	rtn.FavouriteIcon = findIcon([]string{"starred-symbolic", "starred"})
	rtn.DownloadedIcon = findIcon([]string{"emblem-ok-symbolic", "emblem-downloads", "emblem-shared"})
	rtn.DownloadingIcon = findIcon([]string{"emblem-synchronizing-symbolic", "emblem-synchronizing"})
	rtn.DownloadBlockedIcon = findIcon([]string{"action-unavailable-symbolic", "process-stop-symbolic", "changes-prevent-symbolic"})
	rtn.ListStore, rtn.ListStoreRows = rtn.buildListStore()
	rtn.showAllOrFavouritesOnly() // Updates the showRow bool in the list store - could do it while building, but it would duplicates much of toggling the state

	// This is deprecated - should use GtkFilterListModel
	rtn.ListStoreFavouriteFilter = rtn.ListStore.NewFilter(nil).Cast().(*gtk.TreeModelFilter)
	rtn.ListStoreFavouriteFilter.SetVisibleColumn(int(ColumnShowRow))

	// TODO: TreeView is deprecated - should switch to ColumnView at some point
	rtn.TreeView = gtk.NewTreeView()
	rtn.TreeView.AppendColumn(createPixbufColumn("Favourite", ColumnFavourite))
	rtn.TreeView.AppendColumn(createTextColumn("Title", ColumnTitle))
	rtn.TreeView.AppendColumn(createTextColumn("Type", ColumnType))
	rtn.TreeView.AppendColumn(createTextColumn("Duration", ColumnDuration))
	rtn.TreeView.AppendColumn(createTextColumn("Date", ColumnDate))
	rtn.TreeView.AppendColumn(createTextColumn("FTP", ColumnEffectiveFTP))
	rtn.TreeView.AppendColumn(createTextColumn("Max", ColumnEffectiveMax))
	rtn.TreeView.AppendColumn(createPixbufColumn("Downloaded", ColumnVideoDownloaded))
	rtn.TreeView.SetModel(rtn.ListStoreFavouriteFilter)
	rtn.TreeView.SetEnableSearch(false)
	rtn.TreeView.ConnectCursorChanged(rtn.OnIndexSelectionChanged)
	rtn.TreeView.ConnectRowActivated(rtn.OnVideoActivated)

	rtn.KeyController = gtk.NewEventControllerKey()
	rtn.KeyController.ConnectKeyPressed(rtn.OnKeyPress)
	rtn.TreeView.AddController(rtn.KeyController)

	scrollableTree := gtk.NewScrolledWindow()
	scrollableTree.SetHExpand(true)
	scrollableTree.SetVExpand(true)
	scrollableTree.SetChild(rtn.TreeView)

	rtn.SessionPreview = widgets.NewSessionPreview(parent.Profile)
	rtn.SessionPreview.SetVExpand(true)

	backButton := gtk.NewButtonWithLabel("Back")
	backButton.ConnectClicked(rtn.OnBackClicked)

	grid := gtk.NewGrid()
	grid.SetMarginTop(100)
	grid.SetMarginBottom(100)
	grid.SetMarginStart(200)
	grid.SetMarginEnd(200)
	grid.Attach(scrollableTree, 0, 0, 1, 3)
	grid.Attach(rtn.SessionPreview, 0, 3, 1, 2)
	grid.Attach(backButton, 0, 5, 1, 1)
	rtn.Contents = grid

	return rtn
}

func (panel *VideoIndexPanel) OnBackClicked() {
	panel.Parent.Stack.SetVisibleChildName(MainPanelName)
}

func (panel *VideoIndexPanel) getSessionVideoIdFromTreeViewRow(row *gtk.TreePath) string {
	iter, ok := panel.ListStoreFavouriteFilter.Iter(row)
	if !ok {
		fmt.Println("Unable to construct iter")
		return ""
	}
	val := panel.ListStoreFavouriteFilter.Value(iter, ColumnVideoId)
	return val.String()
}

func (panel *VideoIndexPanel) getSessionFromTreeViewRow(row *gtk.TreePath) *feed.SessionDefinition {
	videoId := panel.getSessionVideoIdFromTreeViewRow(row)
	session, ok := feed.Sessions[videoId]
	if !ok {
		fmt.Println("Unrecognised video id?!")
		return nil
	}
	return session
}

func (panel *VideoIndexPanel) OnIndexSelectionChanged() {
	row, _ := panel.TreeView.Cursor()
	session := panel.getSessionFromTreeViewRow(row)
	panel.SessionPreview.ShowSession(session)
}

func (panel *VideoIndexPanel) OnKeyPress(keyval uint, keycode uint, state gdk.ModifierType) bool {
	// fmt.Println("OnKeyPress: ", keyval, keycode, state)
	switch {
	case keyval == 'c':
		panel.toggleAllOrFavouritesOnly()
		return true
	case keyval == '*', keyval == gdk.KEY_Left:
		panel.toggleFavouriteForCurrentRow()
		return true
	case (keyval == 'p') && (state == gdk.ControlMask), (keyval == gdk.KEY_Right):
		row, _ := panel.TreeView.Cursor()
		dialog := powerdialog.NewPowerDialog(&panel.Parent.GtkWindow.Window, panel.Parent.Profile, panel.getSessionVideoIdFromTreeViewRow(row), panel.RefreshPowerLevels)
		dialog.Show()
		return true
	}
	return false
}

func (panel *VideoIndexPanel) OnVideoActivated(row *gtk.TreePath, column *gtk.TreeViewColumn) {
	session := panel.getSessionFromTreeViewRow(row)
	if panel.Parent.FeedCache.State[session.VideoId] != feed.Downloaded {
		fmt.Println("Attempt to play a non-downloaded video: " + session.VideoId)
		return
	}
	panel.Parent.SessionPanel.Play(session)
	panel.Parent.Stack.SetVisibleChildName(SessionPanelName)
}

func (panel *VideoIndexPanel) buildListStore() (*gtk.ListStore, []*gtk.TreeIter) {
	listStore := gtk.NewListStore([]glib.Type{
		glib.TypeString,  // fav
		glib.TypeString,  // title
		glib.TypeString,  // session type
		glib.TypeString,  // video duration
		glib.TypeString,  // video date
		glib.TypeString,  // FTP
		glib.TypeString,  // Max
		glib.TypeString,  // downloaded
		glib.TypeString,  // Video ID
		glib.TypeBoolean, // Show Row
	})
	rows := []*gtk.TreeIter{}
	for _, videoItem := range feed.Index {
		var favIcon string
		if slices.Contains(panel.Parent.Profile.Favourites, videoItem.Id) {
			favIcon = panel.FavouriteIcon
		}
		downloadIcon := panel.downloadIconForVideo(videoItem.Id)
		newRow := listStore.Append()
		listStore.Set(newRow,
			[]int{ColumnFavourite, ColumnTitle, ColumnType, ColumnDuration, ColumnDate, ColumnEffectiveFTP, ColumnEffectiveMax, ColumnVideoDownloaded, ColumnVideoId, ColumnShowRow},
			[]glib.Value{*glib.NewValue(favIcon),
				*glib.NewValue(videoItem.Name),
				*glib.NewValue(videoItem.Type),
				*glib.NewValue(videoItem.Duration),
				*glib.NewValue(videoItem.Date),
				*glib.NewValue(formatPower(panel.Parent.Profile.GetVideoFTP(videoItem.Id, false))),
				*glib.NewValue(formatPower(panel.Parent.Profile.GetVideoMax(videoItem.Id, false))),
				*glib.NewValue(downloadIcon),
				*glib.NewValue(videoItem.Id),
				*glib.NewValue(true),
			})
		rows = append(rows, newRow)
	}
	return listStore, rows
}

func (panel *VideoIndexPanel) RefreshPowerLevels() {
	for i, videoItem := range feed.Index {
		panel.ListStore.SetValue(panel.ListStoreRows[i], int(ColumnEffectiveFTP), glib.NewValue(formatPower(panel.Parent.Profile.GetVideoFTP(videoItem.Id, false))))
		panel.ListStore.SetValue(panel.ListStoreRows[i], int(ColumnEffectiveMax), glib.NewValue(formatPower(panel.Parent.Profile.GetVideoMax(videoItem.Id, false))))
	}
}

func (panel *VideoIndexPanel) RefreshDownloadStateIcons() {
	for i, videoItem := range feed.Index {
		downloadIcon := panel.downloadIconForVideo(videoItem.Id)
		panel.ListStore.SetValue(panel.ListStoreRows[i], int(ColumnVideoDownloaded), glib.NewValue(downloadIcon))
	}
}

func (panel *VideoIndexPanel) downloadIconForVideo(videoId string) string {
	switch panel.Parent.FeedCache.State[videoId] {
	case feed.NotDownloaded:
		return ""
	case feed.DownloadBlocked:
		return panel.DownloadBlockedIcon
	case feed.Downloading:
		return panel.DownloadingIcon
	case feed.Downloaded:
		return panel.DownloadedIcon
	}
	// Should never happen
	return ""
}

func (panel *VideoIndexPanel) toggleAllOrFavouritesOnly() {
	panel.Parent.Profile.ShowFavouritesOnly = !panel.Parent.Profile.ShowFavouritesOnly
	panel.showAllOrFavouritesOnly()
	panel.Parent.Profile.Save()
}

func (panel *VideoIndexPanel) toggleFavouriteForCurrentRow() {
	row, _ := panel.TreeView.Cursor()
	videoId := panel.getSessionVideoIdFromTreeViewRow(row)
	if videoId == "" {
		fmt.Println("Unable to get video id from current row")
		return
	}
	panel.Parent.Profile.ToggleVideoFavourite(videoId)
	panel.Parent.Profile.Save()

	var newFavIconValue string
	if slices.Contains(panel.Parent.Profile.Favourites, videoId) {
		newFavIconValue = panel.FavouriteIcon
	}
	iter, _ := panel.ListStoreFavouriteFilter.Iter(row)
	storeRow := panel.ListStoreFavouriteFilter.ConvertIterToChildIter(iter)
	panel.ListStore.Set(storeRow, []int{ColumnFavourite}, []glib.Value{*glib.NewValue(newFavIconValue)})
}

func (panel *VideoIndexPanel) showAllOrFavouritesOnly() {
	profile := panel.Parent.Profile
	for i, videoItem := range feed.Index {
		var show bool
		if profile.ShowFavouritesOnly {
			show = slices.Contains(profile.Favourites, videoItem.Id)
		} else {
			show = true
		}
		panel.ListStore.SetValue(panel.ListStoreRows[i], int(ColumnShowRow), glib.NewValue(show))
	}
}

func formatPower(power string) string {
	if power == "" {
		return "Dflt"
	}
	return power
}
