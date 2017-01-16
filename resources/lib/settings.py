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
    def getUsername():
        return ADDON.getSetting("username")

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
    def getLastSyncTime():
        return ADDON.getSetting("lastSyncTime")

    @staticmethod
    def setLastSyncTime():
        # Get the current EPOCH time
        epoch = str(int(time.time()))
        ADDON.setSetting("lastSyncTime", epoch)
