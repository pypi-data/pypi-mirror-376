# CHANGELOG.md
## [0.1.10.10] 2025-09-01
 - Fixed notification display after adding DLs.

## [0.1.10.9] 2025-09-01
 - Added file picker option when adding torrents.

## [0.1.10.8] 2025-08-31
 - Fixed bug in right pane of the download options picker.

## [0.1.10.6] 2025-08-31
 - Fixed bug which caused crash due to config key error.
 - Aria2TUI connection now uses a picker spash screen.
   - This fixes pink flash when colours dict changed to the other picker.
 - Improved DL info display.

## [0.1.10.5] 2025-08-29
 - Added to config options: default pane.

## [0.1.10.5] 2025-08-29
 - Added right panes: DL progress, DL Files, DL pieces.

## [0.1.10.0] 2025-08-27
- Feature added: display speed graph of selected download in right pane
- Display selected downloads in right pane when selecting an operation to perform.
  - This was previously done using an infobox but this caused flickering.

## [0.1.9.0] - [0.1.9.21] 2025-08-22
- Fixed error when adding torrent path with ~.
- Fixed crash when adding a non-existent torrent path.
- Fixed cursor displaying after dropping to nvim to add uris/torrents.
- Waiting downloads are now displayed before paused downloads on the "All" mode.
- Ensured compatibility with latest version(s) of listpick:
  - The sort_column is now separate from the select column so we set the selected column in the setOptions picker.
  - The colour theme has to be set for each picker; it does not stay constant after being defined in the first picker.
- Ensured that the display messages are consistent when adding URIs and/or torrents. Previously when URIs were addded it would return the list of GIDs; this has been replaced with a proper message showing how many were added.
- Split batch requests into clumps of 2000 downloads to prevent aria2c throwing an error.

## [0.1.9] 2025-08-08
 - Added download type column.
 - Added uri column.
 - Added header when viewing 'DL Info...'
 - Buxfixes
   - Fixed display of torrent size so that it shows the total size of all files in the torrent.
   - Refresh timer remains the set value after exiting to the menu and returning to the watch downloads Picker.
   - Fixed crash when trying to edit options.
 - Highlight downloads with 'removed' status red.

## [0.1.8] 2025-07-04
 - Added asynchronous data refresh requests using threading--inherited from listpick==0.1.9.
 - Added left-right scrolling using h/l--inherited from listpick==0.1.8.
 - Scroll to home/end with H/L--inherited from listpick==0.1.8.

## [0.1.7] 2025-07-02
 - Added MIT license information.

## [0.1.6] 2025-06-28
 - Restructured project and added it to pypi so that it can be intalled with pip. 
 - Changed default toml location to ~/.config/aria2tui/config.toml

## [0.1.5] 2025-06-27
 - terminal_file_manager option added to config so that the terminal file manager can be modified.
 - gui_file_manager option added to config so that the file manager that is opened in a new window can be modified.
 - launch_command option added to config so that the default file-launcher command can be specified.
 - View data (global or download) options are now passed to a Picker object.
 - Fixed issue with opening location of files that have 0% progress.
 
## [0.1.4] 2025-06-27
 - Ensured that the refresh rate can be set from the config.
 - Change options now uses Picker rather than editing the json from nvim.

## [0.1.3] 2025-06-20
 - Made Aria2TUI class which is called to run the appliction.

## [0.1.2] 2025-06-19
 - *New Feature*: Monitor global and particular download/upload speeds on a graph.
 - Fixed flickering when infobox is shown


## [0.1.1] 2025-06-18
 - Added a global stats string to show the total upload/download speed and the number of active, waiting, and stopped downloads.

## [0.1.0] 2025-06-17
 - CHANGELOG started.
 - Made Aria2TUI compliant with the new class-based Picker.
