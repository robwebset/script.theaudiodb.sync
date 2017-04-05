# -*- coding: utf-8 -*-
import sys
import traceback
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

# Import the common settings
from settings import log
from settings import Settings
from theaudiodb import TheAudioDb
from library import MusicLibrary


ADDON = xbmcaddon.Addon(id='script.theaudiodb.sync')
ADDON_ID = ADDON.getAddonInfo('id')


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

    @staticmethod
    def checkForChangedTrackRatings(username, showProgress=False):
        if not Settings.isUploadTrackRatings():
            return

        trackRatingsPath = xbmc.translatePath('special://profile/addon_data/%s/trackRatings.json' % ADDON_ID).decode("utf-8")
#        albumRatingsFile = xbmc.translatePath('special://profile/addon_data/%s/albumRatings.json' % ADDON_ID).decode("utf-8")

        # Get the existing track from the library database
        musicLib = MusicLibrary()
        libraryTracks = musicLib.getLibraryTracks()

        oldTrackRatings = []
        # Load any existing stored data from disk
        if xbmcvfs.exists(trackRatingsPath):
            # Need to compare tracks to see if any ratings have changed
            try:
                # Load the JSON contents of the file
                oldTrackRatingsFile = xbmcvfs.File(trackRatingsPath, 'r')
                oldTrackRatingsStr = oldTrackRatingsFile.read()
                oldTrackRatingsFile.close()

                # Convert the JSON into objects
                oldTrackRatings = json.loads(oldTrackRatingsStr)

            except:
                log("checkForChangedTrackRatings: Failed to load existing track ratings file: %s" % trackRatingsPath, xbmc.LOGERROR)
                log("checkForChangedTrackRatings: %s" % traceback.format_exc(), xbmc.LOGERROR)

        if (len(libraryTracks) > 0) and (oldTrackRatings > 0):
            theAudioDb = TheAudioDb(username)

            # Loop round all of the current tracks and see if the rating has changed
            # since the last time it was checked
            for currentTrack in libraryTracks:
                # Check if this track has a rating
                existingUserRating = 0
                if 'userrating' in currentTrack:
                    existingUserRating = int(currentTrack['userrating'])

                # If there is no user rating, skip this one
                if existingUserRating == 0:
                    continue

                # Check if this track was in the previously uploaded list
                if ('artist' not in currentTrack) or ('title' not in currentTrack):
                    continue
                if (currentTrack['artist'] in [None, ""]) or (currentTrack['title'] in [None, ""]):
                    continue

                for oldTrack in oldTrackRatings:
                    if ('artist' not in oldTrack) or ('title' not in oldTrack):
                        continue

                    if (oldTrack['artist'] != currentTrack['artist']) or (oldTrack['title'] != currentTrack['title']):
                        continue

                    # Ideally the songId should be the same, but if it's not that could be because the
                    # music was rescanned
                    if currentTrack['songid'] != oldTrack['songid']:
                        log("checkForChangedTrackRatings: Old and new song ids are different old:%s new:%s" % (str(oldTrack['songid']), str(currentTrack['songid'])))

                    # To get here the artist and track are the same, now check if the rating is
                    # different, if so, it has changed since the last time we were run
                    if 'userrating' not in oldTrack:
                        continue
                    if existingUserRating == oldTrack['userrating']:
                        # No change so nothing to do for this track
                        break

                    # At this point the rating has changed, we need to check to ensure the rating
                    # online is the same as the old one, otherwise we might overwrite something
                    # that is newer on-line (on-line takes priority in the case of a clash)
                    rating, totalRating = theAudioDb.getRatingForTrack(currentTrack)

                    # If the on-line rating is the same as the existing rating, nothing to do
                    if rating == existingUserRating:
                        log("checkForChangedTrackRatings: Ratings already the same for song %s" % str(currentTrack['songid']))
                        break
                    if (rating == oldTrack['userrating']) or (rating in [None, ""]):
                        log("checkForChangedTrackRatings: New local rating detected, on-line copy requires update")
                        # Need to update the rating on-line
                        theAudioDb.setRatingForTrack(currentTrack)
                    else:
                        log("checkForChangedTrackRatings: On-line rating has changed, update local with latest online")
                        musicLib.updateLibraryTrackRatings(currentTrack, rating, totalRating)
                        # Update the rating that we have set in the library
                        currentTrack['userrating'] = rating
                    break
            del theAudioDb

        # Now save the updated track information
        try:
            trackRatingsFile = xbmcvfs.File(trackRatingsPath, 'w')
            trackRatingsFile.write(json.dumps(libraryTracks, sort_keys=True, indent=4))
            trackRatingsFile.close()
        except:
            log("checkForChangedTrackRatings: Failed to write file: %s" % trackRatingsPath, xbmc.LOGERROR)
            log("checkForChangedTrackRatings: %s" % traceback.format_exc(), xbmc.LOGERROR)

        del musicLib
