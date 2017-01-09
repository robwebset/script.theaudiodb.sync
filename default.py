# -*- coding: utf-8 -*-
import sys
import urllib2
import traceback
import xbmc
import xbmcgui
import xbmcaddon

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

# Import the common settings
from resources.lib.settings import log
from resources.lib.settings import Settings


ADDON = xbmcaddon.Addon(id='script.theaudiodb.sync')


# Class to handle talking to theaudiodb.com
class TheAudioDb():
    def __init__(self, defaultUsername):
        self.url_prefix = 'http://www.theaudiodb.com/api/v1/json/1/'
        self.cachedTrackRatings = None
        self.cachedAlbumRatings = None
        self.username = defaultUsername

    # Get all the user ratings for tracks
    def _getTrackRatings(self):
        # When we have made the call to get the ratings, we will cache it in
        # memory for future use to save returning to the server each time
        if self.cachedTrackRatings is None:
            # Create the URL to use to get the track ratings
            ratingsUrl = "%sratings-track.php?user=%s" % (self.url_prefix, self.username)

            # Make the call to theaudiodb.com
            json_details = self._makeCall(ratingsUrl)

            if json_details not in [None, ""]:
                json_response = json.loads(json_details)

                # The results of the search come back as an array of entries
                if 'scores' in json_response:
                    self.cachedTrackRatings = []
                    for tracks in json_response['scores']:
                        details = {'mbidTrack': None, 'trackscore': None, 'artist': None, 'track': None, 'tracktotal': None}
                        details['mbidTrack'] = tracks.get('mbidTrack', None)
                        details['artist'] = tracks.get('strArtist', None)
                        details['track'] = tracks.get('strTrack', None)

                        ratingStr = tracks.get('trackscore', None)
                        if ratingStr not in [None, ""]:
                            details['trackscore'] = int(ratingStr)

                        totalStr = tracks.get('tracktotal', None)
                        if totalStr not in [None, ""]:
                            # Total score is a float - so add on 0.5 to ensure the rounding
                            # to an integer is as expected
                            details['tracktotal'] = int(float(totalStr) + 0.5)

                        if (totalStr not in [None, ""]) or (ratingStr not in [None, ""]):
                            # Only add to the list if there is a rating
                            self.cachedTrackRatings.append(details)

        return self.cachedTrackRatings

    # Get all the user ratings for tracks
    def _getAlbumRatings(self):
        # When we have made the call to get the ratings, we will cache it in
        # memory for future use to save returning to the server each time
        if self.cachedAlbumRatings is None:
            # Create the URL to use to get the track ratings
            ratingsUrl = "%sratings-album.php?user=%s" % (self.url_prefix, self.username)

            # Make the call to theaudiodb.com
            json_details = self._makeCall(ratingsUrl)

            if json_details not in [None, ""]:
                json_response = json.loads(json_details)

                # The results of the search come back as an array of entries
                if 'scores' in json_response:
                    self.cachedAlbumRatings = []
                    for tracks in json_response['scores']:
                        details = {'mbidAlbum': None, 'albumscore': None, 'artist': None, 'album': None, 'albumtotal': None}
                        details['mbidAlbum'] = tracks.get('mbidAlbum', None)
                        details['artist'] = tracks.get('strArtist', None)
                        details['album'] = tracks.get('strAlbum', None)

                        ratingStr = tracks.get('albumscore', None)
                        if ratingStr not in [None, ""]:
                            details['albumscore'] = int(ratingStr)

                        totalStr = tracks.get('albumtotal', None)
                        if totalStr not in [None, ""]:
                            # Total score is a float - so add on 0.5 to ensure the rounding
                            # to an integer is as expected
                            details['albumtotal'] = int(float(totalStr) + 0.5)

                        if (totalStr not in [None, ""]) or (ratingStr not in [None, ""]):
                            # Only add to the list if there is a rating
                            self.cachedAlbumRatings.append(details)

        return self.cachedAlbumRatings

    # Given a track from the library will get the rating in theaudiodb.com
    def getRatingForTrack(self, libraryTrack):
        # Get the ratings from theaudiodb
        ratingDetails = self._getTrackRatings()

        # Now look at the library track and see if a match is found
        # first try and match the musicbrainzid
        rating = None
        totalRating = None
        musicbrainztrackid = None
        if 'musicbrainztrackid' in libraryTrack:
            musicbrainztrackid = libraryTrack['musicbrainztrackid']

        if musicbrainztrackid not in [None, ""]:
            # Now check to see if this Id is in our list
            for details in ratingDetails:
                if details['mbidTrack'] == musicbrainztrackid:
                    rating = details['trackscore']
                    totalRating = details['tracktotal']
                    log("Found matching music brainz track id %s (rating: %d)" % (musicbrainztrackid, rating))

        # Check if the track was found using the Id, if not see if we want to
        # use the details instead
        if Settings.isUseArtistDetails() and (rating is None) and (totalRating is None):
            # Check if the rating was not found and we should check for
            # the artist details in order to get a match
            if ('artist' in libraryTrack) and ('title' in libraryTrack):
                if (libraryTrack['artist'] not in [None, ""]) and (libraryTrack['title'] not in [None, ""]):
                    artistName = libraryTrack['artist']
                    # Artist is actually an array of artists
                    if len(libraryTrack['artist']) > 0:
                        artistName = " ".join(libraryTrack['artist'])

                    for details in ratingDetails:
                        # Surround in a try catch, just in case some character encoding
                        # causes some issues
                        try:
                            if (details['artist'].lower() == artistName.lower()) and (details['track'].lower() == libraryTrack['title'].lower()):
                                rating = details['trackscore']
                                totalRating = details['tracktotal']
                                log("Found matching track %s (rating: %d)" % (details['track'], rating))
                        except:
                            log("getRatingForTrack: Failed to compare by artist and track name: %s" % traceback.format_exc())

        return rating, totalRating

    # Given an album from the library will get the rating in theaudiodb.com
    def getRatingForAlbum(self, libraryAlbum):
        # Get the ratings from theaudiodb
        ratingDetails = self._getAlbumRatings()

        # Now look at the library album and see if a match is found
        # first try and match the musicbrainzid
        rating = None
        totalRating = None
        musicbrainzalbumid = None
        if 'musicbrainzalbumid' in libraryAlbum:
            musicbrainzalbumid = libraryAlbum['musicbrainzalbumid']

        if musicbrainzalbumid not in [None, ""]:
            # Now check to see if this Id is in our list
            for details in ratingDetails:
                if details['mbidAlbum'] == musicbrainzalbumid:
                    rating = details['albumscore']
                    totalRating = details['albumtotal']
                    log("Found matching music brainz album id %s (rating: %d)" % (musicbrainzalbumid, rating))

        # Check if the album was found using the Id, if not see if we want to
        # use the details instead
        if Settings.isUseArtistDetails() and (rating is None) and (totalRating is None):
            # Check if the rating was not found and we should check for
            # the artist details in order to get a match
            if ('artist' in libraryAlbum) and ('title' in libraryAlbum):
                if (libraryAlbum['artist'] not in [None, ""]) and (libraryAlbum['title'] not in [None, ""]):
                    artistName = libraryAlbum['artist']
                    # Artist is actually an array of artists
                    if len(libraryAlbum['artist']) > 0:
                        artistName = " ".join(libraryAlbum['artist'])

                    for details in ratingDetails:
                        # Surround in a try catch, just in case some character encoding
                        # causes some issues
                        try:
                            if (details['artist'].lower() == artistName.lower()) and (details['album'].lower() == libraryAlbum['title'].lower()):
                                rating = details['albumscore']
                                totalRating = details['albumtotal']
                                log("Found matching album %s (rating: %d)" % (details['album'], rating))
                        except:
                            log("getRatingForAlbum: Failed to compare by artist and album name: %s" % traceback.format_exc())

        return rating, totalRating

    # Perform the API call
    def _makeCall(self, url):
        log("makeCall: Making query using %s" % url)
        resp_details = None
        try:
            req = urllib2.Request(url)
            req.add_header('Accept', 'application/json')
            response = urllib2.urlopen(req)
            resp_details = response.read()
            try:
                response.close()
                log("makeCall: Request returned %s" % resp_details)
            except:
                pass
        except:
            log("makeCall: Failed to retrieve details from %s: %s" % (url, traceback.format_exc()))

        return resp_details


# Class to handle calls to the Kodi Music Library
class MusicLibrary():
    def __init__(self, kodiMajorVersion, ratingDivisor):
        self.kodiMajorVersion = kodiMajorVersion
        self.ratingDivisor = ratingDivisor
        self.additionalTrackValues = ''
        self.ratingName = 'rating'
        if kodiMajorVersion >= 17:
            self.additionalTrackValues = ', "userrating"'
            self.ratingName = 'userrating'
        # Check if we may want to use the Artist Details as well
        if Settings.isUseArtistDetails():
            self.additionalTrackValues = '%s, "title", "artist"' % self.additionalTrackValues

    # Get details about every track in the Kodi Music Library
    def getLibraryTracks(self):
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": {"properties": ["musicbrainztrackid", "rating"%s]  }, "id": "libSongs"}' % self.additionalTrackValues)
        json_response = json.loads(json_query)

        libraryTracks = []
        if ("result" in json_response) and ('songs' in json_response['result']):
            libraryTracks = json_response['result']['songs']

        log("MusicLibrary: Retrieved a total of %d tracks" % len(libraryTracks))
        return libraryTracks

    # Get details about every track in the Kodi Music Library
    def getLibraryAlbums(self):
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": {"properties": ["musicbrainzalbumid", "rating"%s]  }, "id": "libSongs"}' % self.additionalTrackValues)
        json_response = json.loads(json_query)

        libraryAlbums = []
        if ("result" in json_response) and ('albums' in json_response['result']):
            libraryAlbums = json_response['result']['albums']

        log("MusicLibrary: Retrieved a total of %d albums" % len(libraryAlbums))
        return libraryAlbums

    # Update the rating for a given track
    def updateLibraryTrackRatings(self, libTrack, rating, totalRating):
        # Make sure the song Id is set, otherwise we have nothing to update
        if (libTrack in [None, ""]) or ('songid' not in libTrack) or (libTrack['songid'] in [None, ""]):
            return

        songid = libTrack['songid']

        valuesToSet = ""
        existingRating = 0
        if 'rating' in libTrack:
            existingRating = int(libTrack['rating'])

        if self.kodiMajorVersion >= 17:
            # Check if the main rating needs to be updated
            if (totalRating not in [None, "", 0]) and (totalRating != existingRating):
                valuesToSet = ', "rating": %d' % totalRating
            # Check if the user rating needs updating
            existingUserRating = 0
            if 'userrating' in libTrack:
                existingUserRating = int(libTrack['userrating'])
            if (rating not in [None, "", 0]) and (rating != existingUserRating):
                valuesToSet = '%s, "userrating": %d' % (valuesToSet, rating)
        else:
            # For older kodi versions we update the rating with the user rating
            if rating not in [None, "", 0]:
                correctedRating = int(rating / self.ratingDivisor)
                if correctedRating != existingRating:
                    valuesToSet = ', "rating": %d' % correctedRating

        trackUpdated = False
        # Check if we have any values to update
        if valuesToSet in [None, ""]:
            log("updateLibraryTrackRatings: no ratings to update, songid:%s, rating:%s, totalRating:%s" % (songid, str(rating), str(totalRating)))
        else:
            log("updateLibraryTrackRatings: updating songid %s with%s" % (songid, valuesToSet))
            setJson = '{"jsonrpc": "2.0", "method": "AudioLibrary.SetSongDetails", "params": { "songid": %s%s }, "id": "libSongs"}' % (songid, valuesToSet)
            xbmc.executeJSONRPC(setJson)
            trackUpdated = True

        return trackUpdated

    # Update the rating for a given album
    def updateLibraryAlbumRatings(self, libAlbum, rating, totalRating):
        # Make sure the song Id is set, otherwise we have nothing to update
        if (libAlbum in [None, ""]) or ('albumid' not in libAlbum) or (libAlbum['albumid'] in [None, ""]):
            return

        albumid = libAlbum['albumid']

        valuesToSet = ""
        existingRating = 0
        if 'rating' in libAlbum:
            existingRating = int(libAlbum['rating'])

        if self.kodiMajorVersion >= 17:
            # Check if the main rating needs to be updated
            if (totalRating not in [None, "", 0]) and (totalRating != existingRating):
                valuesToSet = ', "rating": %d' % totalRating
            # Check if the user rating needs updating
            existingUserRating = 0
            if 'userrating' in libAlbum:
                existingUserRating = int(libAlbum['userrating'])
            if (rating not in [None, "", 0]) and (rating != existingUserRating):
                valuesToSet = '%s, "userrating": %d' % (valuesToSet, rating)
        else:
            # For older kodi versions we update the rating with the user rating
            if rating not in [None, "", 0]:
                correctedRating = int(rating / self.ratingDivisor)
                if correctedRating != existingRating:
                    valuesToSet = ', "rating": %d' % correctedRating

        albumUpdated = False
        # Check if we have any values to update
        if valuesToSet in [None, ""]:
            log("updateLibraryAlbumRatings: no ratings to update, albumid:%s, rating:%s, totalRating:%s" % (albumid, str(rating), str(totalRating)))
        else:
            log("updateLibraryAlbumRatings: updating albumid %s with%s" % (albumid, valuesToSet))
            setJson = '{"jsonrpc": "2.0", "method": "AudioLibrary.SetAlbumDetails", "params": { "albumid": %s%s }, "id": "libSongs"}' % (albumid, valuesToSet)
            xbmc.executeJSONRPC(setJson)
            albumUpdated = True

        return albumUpdated


##################################
# Main of TheAudioDBSync Script
##################################
if __name__ == '__main__':
    log("TheAudioDBSync Starting %s" % ADDON.getAddonInfo('version'))

    # Each version of Kodi stores the ratings slightly differently so before
    # we do anything find out which version is running
    kodiVer = xbmc.getInfoLabel('system.buildversion')
    majorVersion = 17
    minorVersion = 0
    try:
        majorVersion = int(kodiVer.split(".", 1)[0])
    except:
        log("Failed to get major version, using %d" % majorVersion)
    try:
        minorSplit = kodiVer.split(".", 2)[1]
        # Non GA versions there are bits after a minus
        minorVersion = int(minorSplit.split("-", 1)[0])
    except:
        log("Failed to get minor version, using %d" % minorVersion)

    # Looks like Jarvis (v16.0) and earlier are 1-5, otherwise 1-10
    ratingDivisor = 1
    if (majorVersion < 16) or ((majorVersion < 17) and (minorVersion < 1)):
        log("Detected version earlier than 16.1, using rating range 1-5")
        ratingDivisor = 2

    # Get the username
    username = Settings.getUsername()

    if username in [None, ""]:
        # Show a dialog detailing that the username is not set
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32005))
    else:
        theAudioDb = TheAudioDb(username)
        musicLib = MusicLibrary(majorVersion, ratingDivisor)

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

        # Display a summary of what was performed
        summaryAlbums = "%d %s" % (numAlbumsUpdated, ADDON.getLocalizedString(32010))
        summaryTracks = "%d %s" % (numTracksUpdated, ADDON.getLocalizedString(32011))
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), summaryAlbums, summaryTracks)

        del musicLib
        del theAudioDb

    log("TheAudioDBSync Finished")
