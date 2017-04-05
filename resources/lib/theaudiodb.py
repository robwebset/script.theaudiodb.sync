# -*- coding: utf-8 -*-
import sys
import urllib
import urllib2
import base64
import traceback

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

# Import the common settings
from settings import log
from settings import Settings


# Class to handle talking to theaudiodb.com
class TheAudioDb():
    def __init__(self, defaultUsername):
        self.url_prefix = base64.b64decode('aHR0cDovL3d3dy50aGVhdWRpb2RiLmNvbS9hcGkvdjEvanNvbi82NjE5NjdkODMyMDIzMjQ3MTUzOTg0Lw==')
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
                    if json_response['scores'] not in [None, '']:
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

            # Check for the case where the site is unreachable
            if self.cachedTrackRatings is None:
                self.cachedTrackRatings = []

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
                    if json_response['scores'] not in [None, '']:
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

            # Check for the case where the site is unreachable
            if self.cachedAlbumRatings is None:
                self.cachedAlbumRatings = []

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
            req.add_header('User-Agent', 'Kodi Browser')
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

    def setRatingForTrack(self, trackDetails):
        log("setRatingForTrack: Setting rating for songId: %s" % str(trackDetails['songid']))
        ratingsUrl = "%ssubmit-track2.php?user=%s" % (self.url_prefix, self.username)

        if 'artist' in trackDetails:
            if trackDetails['artist'] not in [None, ""]:
                fullArtist = urllib.quote_plus(" ".join(trackDetails['artist']))
                ratingsUrl = "%s&artist=%s" % (ratingsUrl, fullArtist)

        # "&album={album}"

        if 'title' in trackDetails:
            if trackDetails['title'] not in [None, ""]:
                ratingsUrl = "%s&track=%s" % (ratingsUrl, urllib.quote_plus(trackDetails['title']))

        if 'userrating' in trackDetails:
            if trackDetails['userrating'] not in [None, ""]:
                ratingsUrl = "%s&rating=%s" % (ratingsUrl, trackDetails['userrating'])

        ratingsUrl = "%s&api=%s" % (ratingsUrl, Settings.getApiToken())

        # Make the call to theaudiodb.com
        json_details = self._makeCall(ratingsUrl)

        success = False
        errorMsg = None
        if json_details not in [None, ""]:
            json_response = json.loads(json_details)
            if 'result' in json_response:
                errorMsg = json_response['result']
                if errorMsg not in [None, '']:
                    log("setRatingForTrack: Setting rating response was: %s" % errorMsg)
                    if errorMsg.startswith('SUCCESS'):
                        success = True

        return success, errorMsg
