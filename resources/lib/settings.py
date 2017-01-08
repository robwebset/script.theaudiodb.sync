# -*- coding: utf-8 -*-
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
    def getUsername():
        return ADDON.getSetting("username")

    @staticmethod
    def isUseArtistDetails():
        return ADDON.getSetting("useArtistDetails") == "true"
