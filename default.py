# -*- coding: utf-8 -*-
import time
import xbmcgui
import xbmcaddon

# Import the common settings
from resources.lib.settings import log
from resources.lib.settings import Settings
from resources.lib.sync import LibrarySync
from resources.lib.summary import Summary


ADDON = xbmcaddon.Addon(id='script.theaudiodb.sync')


##################################
# Main of TheAudioDBSync Script
##################################
if __name__ == '__main__':
    log("TheAudioDBSync Starting %s" % ADDON.getAddonInfo('version'))

    # Get the username
    username = Settings.getUsername()

    if username in [None, ""]:
        # Show a dialog detailing that the username is not set
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32005))
    else:
        dialogSummary = ''

        # Make the call to upload any ratings that have changed
        numAlbumRatingsUploaded = -1
        if Settings.isUploadAlbumRatings():
            numAlbumRatingsUploaded = LibrarySync.checkForChangedAlbumRatings(username, True)

        numTrackRatingsUploaded = -1
        if Settings.isUploadTrackRatings():
            numTrackRatingsUploaded = LibrarySync.checkForChangedTrackRatings(username, True)

        if (numTrackRatingsUploaded != -1) or (numAlbumRatingsUploaded != -1):
            if numAlbumRatingsUploaded < 0:
                numAlbumRatingsUploaded = 0
            if numTrackRatingsUploaded < 0:
                numTrackRatingsUploaded = 0

            # Display a summary of what was performed
            dialogSummary = "%d %s\n%d %s\n" % (numAlbumRatingsUploaded, ADDON.getLocalizedString(32030), numTrackRatingsUploaded, ADDON.getLocalizedString(32031))

        # Only check for resync if it is enabled
        if Settings.isUpdateAlbumRatings() or Settings.isUpdateTrackRatings():
            performResync = True
            # Before performing the resync, check when the last time a resync was done, we want
            # to try and discourage people doing too many resyncs in quick succession
            lastResyncTimeStr = Settings.getLastSyncTime()
            if lastResyncTimeStr not in [None, ""]:
                currentTime = int(time.time())
                # check if the last resync was within 5 minutes
                if currentTime < (int(lastResyncTimeStr) + 300):
                    performResync = xbmcgui.Dialog().yesno(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32016))

            if performResync:
                # Perform the resync operation and display the status
                numAlbumsUpdated, numTracksUpdated = LibrarySync.syncToLibrary(username, True)

                # Display a summary of what was performed
                dialogSummary += "%d %s\n%d %s" % (numAlbumsUpdated, ADDON.getLocalizedString(32010), numTracksUpdated, ADDON.getLocalizedString(32011))

        # Check if the summary should be saved
        if Settings.isSummaryLogEnabled():
            summary = Summary()
            summary.saveToDisk()
            del summary

        if dialogSummary not in [None, ""]:
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), dialogSummary)

    log("TheAudioDBSync Finished")
