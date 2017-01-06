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
    def __init__(self):
        self.url_prefix = 'http://www.theaudiodb.com/api/v1/json/1/'

    def getTrackRatings(self, username):
        # Create the URL to use to get the track ratings
        ratingsUrl = "%sratings-track.php?user=%s" % (self.url_prefix, username)

        # Make the call to theaudiodb.com
        json_details = self._makeCall(ratingsUrl)

        trackRatings = {}
        if json_details not in [None, ""]:
            json_response = json.loads(json_details)

            # The results of the search come back as an array of entries
            if 'scores' in json_response:
                for tracks in json_response['scores']:
                    mbidTrack = tracks.get('mbidTrack', None)
                    if mbidTrack not in [None, ""]:
                        mbidTrack = str(mbidTrack)
                        ratingStr = tracks.get('trackscore', None)
                        if mbidTrack not in [None, ""]:
                            log("TrackRatings: Found Id %s with rating %s" % (mbidTrack, str(ratingStr)))
                            trackRatings[mbidTrack] = int(ratingStr)

        return trackRatings

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
    def __init__(self, kodiMajorVersion):
        self.ratingName = 'rating'
        if kodiMajorVersion == 17:
            self.ratingName = 'userrating'

    # Get details about every track in the Kodi Music Library
    def getLibraryTracks(self):
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": {"properties": ["musicbrainztrackid", "%s"]  }, "id": "libSongs"}' % self.ratingName)
        json_response = json.loads(json_query)

        libraryTracks = []
        if ("result" in json_response) and ('songs' in json_response['result']):
            libraryTracks = json_response['result']['songs']

        log("MusicLibrary: Retrieved a total of %d tracks" % len(libraryTracks))

        return libraryTracks

    # Set the rating for a given track
    def setLibraryTrackRating(self, songid, rating):
        setJson = '{"jsonrpc": "2.0", "method": "AudioLibrary.SetSongDetails", "params": { "songid": %s, "%s": %d  }, "id": "libSongs"}' % (songid, self.ratingName, rating)
        xbmc.executeJSONRPC(setJson)


##################################
# Main of TheAudioDB Script
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
        theAudioDb = TheAudioDb()
        ratings = theAudioDb.getTrackRatings(username)
        del theAudioDb

        # For each rating, check to see if the track appears in the library
        # TODO: At the moment it only works if the library is scanned with musicbrainztrackid
        #       it should also have the option to search via the artist name and track title
        # TODO: Add busy dialog / Progress bar
        # TODO: Allow running as service
        # TODO: Add option to record when the last update was performed and only do newer changes
        # TODO: For v17 allow the rating to be read from theaudioDB (in addition to the userrating)
        #       http://www.theaudiodb.com/api/v1/json/1/track-mb.php?i=e4c0494d-5ab6-479a-a527-cfdc41f7c595

        # Unfortunately we can not filter based on the musicbrainztrackid as that is not a valid filter support
        # this means we just have to get all tracks!!!
        # TODO: Is there a better way of doing this

        musicLib = MusicLibrary(majorVersion)
        libraryTracks = musicLib.getLibraryTracks()

        for libTrack in libraryTracks:
            if 'musicbrainztrackid' in libTrack:
                musicbrainztrackid = libTrack['musicbrainztrackid']
                if musicbrainztrackid in ratings:
                    songid = libTrack['songid']
                    log("Found matching music brainz track id %s (%s)" % (musicbrainztrackid, songid))
                    existingRating = 0
                    if 'rating' in libTrack:
                        existingRating = int(libTrack['rating'])
                    if 'userrating' in libTrack:
                        existingRating = int(libTrack['userrating'])

                    # Check if the rating has changed
                    if existingRating == ratings[musicbrainztrackid]:
                        log("Ratings are currently the same (%d), skipping %s" % (existingRating, musicbrainztrackid))
                    else:
                        log("Setting rating to %d (was %d)" % (ratings[musicbrainztrackid], existingRating))
                        musicLib.setLibraryTrackRating(songid, int(ratings[musicbrainztrackid] / ratingDivisor))

        del musicLib

    log("TheAudioDBSync Finished")
