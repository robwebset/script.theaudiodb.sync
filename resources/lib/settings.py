# -*- coding: utf-8 -*-
import time
import xbmc
import xbmcaddon

ADDON = xbmcaddon.Addon(id='script.theaudiodb.sync')
ADDON_ID = ADDON.getAddonInfo('id')


# Common logging module
def log(txt, loglevel=xbmc.LOGDEBUG):
    if (ADDON.getSetting("logEnabled") == "true") or (loglevel != xbmc.LOGDEBUG):
        if isinstance(txt, str):
            txt = txt.decode("utf-8")
        message = u'%s: %s' % (ADDON_ID, txt)
        xbmc.log(msg=message.encode("utf-8"), level=loglevel)


##############################
# Stores Various Settings
##############################
class Settings():
    @staticmethod
    def getKodiVersion():
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

        return majorVersion, minorVersion

    @staticmethod
    def isSummaryLogEnabled():
        return ADDON.getSetting("summaryLogEnabled") == "true"

    @staticmethod
    def getUsername():
        return ADDON.getSetting("username")

    @staticmethod
    def getApiToken():
        return ADDON.getSetting("apiToken")

    @staticmethod
    def isUseArtistDetails():
        return ADDON.getSetting("useArtistDetails") == "true"

    @staticmethod
    def isUpdateAlbumRatings():
        return ADDON.getSetting("updateAlbumRatings") == "true"

    @staticmethod
    def isUpdateTrackRatings():
        return ADDON.getSetting("updateTrackRatings") == "true"

    @staticmethod
    def isUploadAlbumRatings():
        if Settings.getApiToken() in [None, ""]:
            return False
        return ADDON.getSetting("uploadAlbumRatings") == "true"

    @staticmethod
    def isUploadTrackRatings():
        if Settings.getApiToken() in [None, ""]:
            return False
        return ADDON.getSetting("uploadTrackRatings") == "true"

    @staticmethod
    def isUploadRatingsOnStartup():
        if Settings.getApiToken() in [None, ""]:
            return False
        return ADDON.getSetting("uploadRatingsOnStartup") == "true"

    @staticmethod
    def doNotUploadZeroRatings():
        if Settings.getApiToken() in [None, ""]:
            return True
        return ADDON.getSetting("doNotUploadZeroRatings") == "true"

    @staticmethod
    def getLastSyncTime():
        return ADDON.getSetting("lastSyncTime")

    @staticmethod
    def setLastSyncTime(setDisplayTime=False):
        # Get the current EPOCH time
        epoch = str(int(time.time()))
        ADDON.setSetting("lastSyncTime", epoch)
        # Also set the display time if required
        if setDisplayTime:
            ADDON.setSetting("lastSyncDisplay", time.strftime('%H:%M:%S %Y-%m-%d', time.localtime(float(epoch))))

    @staticmethod
    def getNextScheduledResyncTime():
        index = int(ADDON.getSetting("scheduleInterval"))
        if index == 0:
            return None

        lastResyncStr = Settings.getLastSyncTime()
        if lastResyncStr in [None, "", "0"]:
            log("getNextScheduledResyncTime: No sync time set, using current")
            # Set the current time as the last resync as this will trigger in the future
            Settings.setLastSyncTime(False)
            return None

        if index == 1:
            # Weekly (604,800 seconds)
            return int(lastResyncStr) + 604800
        elif index == 2:
            # Fortnightly (1,209,600 seconds)
            return int(lastResyncStr) + 1209600
        elif index == 3:
            # Monthly (2,592,000 seconds) so 30 days
            return int(lastResyncStr) + 2592000

    @staticmethod
    def isScheduleDisplayProgress():
        return ADDON.getSetting("scheduleDisplayProgress") == "true"
