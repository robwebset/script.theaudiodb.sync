# -*- coding: utf-8 -*-
import sys
import xbmc

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

# Import the common settings
from settings import log
from settings import Settings


# Class to handle calls to the Kodi Music Library
class MusicLibrary():
    def __init__(self):
        # Each version of Kodi stores the ratings slightly differently so before
        # we do anything find out which version is running
        self.kodiMajorVersion, kodiMinorVersion = Settings.getKodiVersion()

        # Looks like Jarvis (v16.0) and earlier are 1-5, otherwise 1-10
        self.ratingDivisor = 1
        if (self.kodiMajorVersion < 16) or ((self.kodiMajorVersion < 17) and (kodiMinorVersion < 1)):
            log("Detected version earlier than 16.1, using rating range 1-5")
            self.ratingDivisor = 2

        self.additionalTrackValues = ''
        self.ratingName = 'rating'
        if self.kodiMajorVersion >= 17:
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
