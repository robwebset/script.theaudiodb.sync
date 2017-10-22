# -*- coding: utf-8 -*-
import traceback
import xbmc
import xbmcaddon
import xbmcvfs


ADDON = xbmcaddon.Addon(id='script.theaudiodb.sync')
ADDON_ID = ADDON.getAddonInfo('id')

from settings import log


##############################
# Stores Progress Summary
##############################
class Summary():
    # Store the items globally, all instances should store their items together until they are saved to disk
    _items = []
    F_UNKNOWN = 'UNKNOWN'
    F_UPLOAD = 'UPLOAD'
    F_DOWNLOAD = 'DOWNLOAD'
    A_UNKNOWN = 'UNKNOWN'
    A_TRACK = 'TRACK'
    A_ALBUM = 'ALBUM'

    def __init__(self):
        self.current = None
        self.clearCurrent()

    def saveCurrent(self):
        Summary._items.append(self.current.copy())
        self.clearCurrent()

    def clearCurrent(self):
        self.current = {'function': Summary.F_UNKNOWN, 'area': Summary.A_UNKNOWN, 'artist': '', 'title': '', 'oldRating': -1, 'newRating': -1, 'result': 'No change'}

    def saveToDisk(self):
        log("saveToDisk: Saving summary to disk")
        logPath = xbmc.translatePath('special://profile/addon_data/%s/sync_summary.log' % ADDON_ID).decode("utf-8")

        if len(Summary._items) < 1:
            log("saveToDisk: No items in the summary")
            return

        allData = 'OPERATION|AREA|ARTIST|TITLE|OLD or TOTAL RATING|NEW RATING|RESULT\n'
        for item in Summary._items:
            allItems = []
            if item['function'] is None:
                allItems.append('')
            else:
                allItems.append(item['function'])
            if item['area'] is None:
                allItems.append('')
            else:
                allItems.append(item['area'])
            if item['artist'] is None:
                allItems.append('')
            else:
                allItems.append(item['artist'])
            if item['title'] is None:
                allItems.append('')
            else:
                allItems.append(item['title'])
            if item['oldRating'] is None:
                allItems.append('')
            else:
                allItems.append(str(item['oldRating']))
            if item['newRating'] is None:
                allItems.append('')
            else:
                allItems.append(str(item['newRating']))
            if item['result'] is None:
                allItems.append('')
            else:
                allItems.append(item['result'])
            allData += '|'.join(allItems)
            allData += '\n'

        try:
            logFile = xbmcvfs.File(logPath, 'wb')
            logFile.write(bytearray(allData, 'utf_8'))
            logFile.close()
        except:
            log("saveToDisk: Failed to write file: %s" % logPath, xbmc.LOGERROR)
            log("saveToDisk: %s" % traceback.format_exc(), xbmc.LOGERROR)

        Summary._items = []

    def reset(self):
        Summary._items = []
