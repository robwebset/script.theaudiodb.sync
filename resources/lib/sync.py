# -*- coding: utf-8 -*-
import xbmcgui
import xbmcaddon

# Import the common settings
from settings import log
from settings import Settings
from theaudiodb import TheAudioDb
from library import MusicLibrary


ADDON = xbmcaddon.Addon(id='script.theaudiodb.sync')


# A dummy implementation of the progress dialog, means the code
# remains simple for cases where no progress is required
class DummyProgress():
    def create(self, arg1=None, arg2=None):
        pass

    def update(self, percent=None, message=None):
        pass

    def close(self):
        pass


# Main controller class that performs the Sync
class LibrarySync():
    @staticmethod
    def syncToLibrary(username, showProgress=False):
        log("syncToLibrary: Performing sysnc for user = %s" % username)

        # Store the time that the resync was last performed, we do this at the start
        # and the end as it may take a while and we want it set early so we can stop
        # another sync being performed when another is in progress
        Settings.setLastSyncTime()

        theAudioDb = TheAudioDb(username)
        musicLib = MusicLibrary()

        # Counters for the amount of data updated
        numTracksUpdated = 0
        numAlbumsUpdated = 0

        # Check if the progress dialog should be shown
        progressDialog = DummyProgress()
        if showProgress:
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
        Settings.setLastSyncTime(True)

        del musicLib
        del theAudioDb

        log("syncToLibrary: Albums Updated = %d, Tracks Updated = %d" % (numAlbumsUpdated, numTracksUpdated))

        return numAlbumsUpdated, numTracksUpdated
