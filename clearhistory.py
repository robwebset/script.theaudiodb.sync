# -*- coding: utf-8 -*-
import traceback
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui

# Import the common settings
from resources.lib.settings import log

ADDON = xbmcaddon.Addon(id='script.theaudiodb.sync')
ADDON_ID = ADDON.getAddonInfo('id')


#########################
# Main
#########################
if __name__ == '__main__':
    log("AudioDBSync: Clear History Called (version %s)" % ADDON.getAddonInfo('version'))

    trackRatingsPath = xbmc.translatePath('special://profile/addon_data/%s/trackRatings.json' % ADDON_ID).decode("utf-8")
    albumRatingsPath = xbmc.translatePath('special://profile/addon_data/%s/albumRatings.json' % ADDON_ID).decode("utf-8")

    if xbmcvfs.exists(trackRatingsPath):
        try:
            log("AudioDBSync: Removing file %s" % trackRatingsPath)

            xbmcvfs.delete(trackRatingsPath)
        except:
            log("AudioDBSync: %s" % traceback.format_exc(), xbmc.LOGERROR)

    if xbmcvfs.exists(albumRatingsPath):
        try:
            log("AudioDBSync: Removing file %s" % albumRatingsPath)

            xbmcvfs.delete(albumRatingsPath)
        except:
            log("AudioDBSync: %s" % traceback.format_exc(), xbmc.LOGERROR)

    xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32034))
