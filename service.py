# -*- coding: utf-8 -*-
import time
import xbmcaddon

# Import the common settings
from resources.lib.settings import log
from resources.lib.settings import Settings
from resources.lib.sync import LibrarySync


ADDON = xbmcaddon.Addon(id='script.theaudiodb.sync')


##################################
# Main of TheAudioDBSync Script
##################################
if __name__ == '__main__':
    log("TheAudioDBSync Service Starting %s" % ADDON.getAddonInfo('version'))

    # Get the username
    username = Settings.getUsername()

    # If the username is not set, then nothing to do yet
    if username not in [None, ""]:
        performResync = False

        if Settings.isUploadRatingsOnStartup():
            LibrarySync.checkForChangedTrackRatings(username, False)
            LibrarySync.checkForChangedAlbumRatings(username, False)

        # Only check for resync if it is enabled
        if Settings.isUpdateAlbumRatings() or Settings.isUpdateTrackRatings():
            nextResyncTime = Settings.getNextScheduledResyncTime()

            if nextResyncTime not in [None, "", "0"]:
                log("Service: Next Sync time is %d" % nextResyncTime)
                currentTime = int(time.time())
                log("Service: Current time is %d" % currentTime)
                # check if the last resync was within 5 minuted
                if currentTime > nextResyncTime:
                    performResync = True

        if performResync:
            # Check if the status should be displayed
            displayProgress = Settings.isScheduleDisplayProgress()
            # Perform the resync operation and display the status
            numAlbumsUpdated, numTracksUpdated = LibrarySync.syncToLibrary(username, displayProgress)

    log("TheAudioDBSync Service Finished")
