# -*- coding: utf-8 -*-
import xbmcgui
import xbmcaddon

# Import the common settings
from resources.lib.settings import log
from resources.lib.settings import Settings
from resources.lib.theaudiodb import TheAudioDb
from resources.lib.library import MusicLibrary


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
        theAudioDb = TheAudioDb(username)
        musicLib = MusicLibrary()

        # Counters for the amount of data updated
        numTracksUpdated = 0
        numAlbumsUpdated = 0

        progressDialog = xbmcgui.DialogProgressBG()
        try:
            progressDialog.create(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32007))

            # Unfortunately we can not filter based on the musicbrainztrackid as that is not a
            # valid filter support this means we just have to get all tracks
            libraryTracks = []
            if Settings.isUpdateTrackRatings():
                libraryTracks = musicLib.getLibraryTracks()

            # Set the percentage that it takes to get all the tracks from the library
            # at about 5% for now
            currentPercent = float(5)

            # Now that we have an idea of the number of tracks that there are to
            # process we can give a better idea of the progress
            displayMsg = "%d %s" % (len(libraryTracks), ADDON.getLocalizedString(32008))
            progressDialog.update(percent=int(currentPercent), message=displayMsg)

            # Now get the album details
            libraryAlbums = []
            if Settings.isUpdateAlbumRatings():
                libraryAlbums = musicLib.getLibraryAlbums()

            # Set the percentage that it takes to get all the albums from the library
            # at about 5% for now
            currentPercent = float(10)

            # Calculate the percentage progress that each track will be
            perItemPercent = float((float(len(libraryTracks) + len(libraryAlbums))) / float(90))

            if len(libraryTracks) > 0:
                # For each rating, check to see if the track appears in the library
                for libTrack in libraryTracks:
                    # Get the ratings for this track
                    rating, totalRating = theAudioDb.getRatingForTrack(libTrack)
                    # Perform the library update for this track
                    trackUpdated = musicLib.updateLibraryTrackRatings(libTrack, rating, totalRating)
                    if trackUpdated:
                        numTracksUpdated = numTracksUpdated + 1
                    currentPercent = float(currentPercent + perItemPercent)
                    progressDialog.update(percent=int(currentPercent))

            if len(libraryAlbums) > 0:
                # Set the progress bar to state that we are processing the albums
                displayMsg = "%d %s" % (len(libraryAlbums), ADDON.getLocalizedString(32009))
                progressDialog.update(percent=int(currentPercent), message=displayMsg)

                # Process the albums
                for libAlbum in libraryAlbums:
                    # Get the ratings for this album
                    rating, totalRating = theAudioDb.getRatingForAlbum(libAlbum)
                    # Perform the library update for this album
                    albumUpdated = musicLib.updateLibraryAlbumRatings(libAlbum, rating, totalRating)
                    if albumUpdated:
                        numAlbumsUpdated = numAlbumsUpdated + 1
                    currentPercent = float(currentPercent + perItemPercent)
                    progressDialog.update(percent=int(currentPercent))

        finally:
            progressDialog.close()

        # Store the time that the resync was last performed
        Settings.setLastSyncTime()

        # Display a summary of what was performed
        summaryAlbums = "%d %s" % (numAlbumsUpdated, ADDON.getLocalizedString(32010))
        summaryTracks = "%d %s" % (numTracksUpdated, ADDON.getLocalizedString(32011))
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), summaryAlbums, summaryTracks)

        del musicLib
        del theAudioDb

    log("TheAudioDBSync Finished")
