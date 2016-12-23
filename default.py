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


ADDON = xbmcaddon.Addon(id='script.theaudiodb')


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


##################################
# Main of TheAudioDB Script
##################################
if __name__ == '__main__':
    log("TheAudioDB Starting %s" % ADDON.getAddonInfo('version'))

    # TODO: Get the version of Kodi and decide if the Kodi rating is 1-5 or 1-10
    # Looks like Jarvis (v16.0) and earlier are 1-5, otherwise 1-10
    # Check if later Jarvis versions (v16.1) uses 5 or 10 as the max
    ratingDivisor = 1

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
        # TODO: Add busy dialog
        # TODO: Allow running as service
        # TODO: Add option to record when the last update was performed and only do newer changes

        # Unfortunately we can not filter based on the musicbrainztrackid as that is not a valid filter support
        # this means we just have to get all tracks!!!
        # TODO: Is there a better way of doing this

        # TODO: Also get the current rating and only do the update if it is different
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": {"properties": ["musicbrainztrackid"]  }, "id": "libSongs"}')
        json_response = json.loads(json_query)

        if ("result" in json_response) and ('songs' in json_response['result']):
            libraryTracks = json_response['result']['songs']
            for libTrack in libraryTracks:
                if 'musicbrainztrackid' in libTrack:
                    musicbrainztrackid = libTrack['musicbrainztrackid']
                    if musicbrainztrackid in ratings:
                        songid = libTrack['songid']
                        log("Found matching music brainz track id %s (%s)" % (musicbrainztrackid, songid))
                        log("Setting rating to %d" % ratings[musicbrainztrackid])
                        # Now update rating for this track
                        setJson = '{"jsonrpc": "2.0", "method": "AudioLibrary.SetSongDetails", "params": { "songid": %s, "rating": %d  }, "id": "libSongs"}' % (songid, int(ratings[musicbrainztrackid] / ratingDivisor))
                        json_query = xbmc.executeJSONRPC(setJson)
                        json_response = json.loads(json_query)

    log("TheAudioDB Finished")
