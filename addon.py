import os
import sys

import xbmc
import xbmcaddon
import xbmcgui
import json

monitor = xbmc.Monitor()
player = xbmc.Player()

__addon_id__ = 'script.valerion.cinema'
__addon = xbmcaddon.Addon(__addon_id__)
__icon__ = __addon.getAddonInfo('icon')

def notify(msg):
    xbmcgui.Dialog().notification("Valerion Cinema", msg, __icon__, 3000)

def warn(msg):
    xbmcgui.Dialog().notification("Valerion Cinema", msg, xbmcgui.NOTIFICATION_WARNING, 5000)

class Player(xbmc.Player):
    def __init__(self):
        xbmc.Player.__init__(self)

    def onAVStarted(self):
        if not player.isPlayingVideo:
            return
        
        scope_screen_aspect = float(xbmcaddon.Addon().getSetting("screen_ar"))
        standard_screen_aspect = 16/9

        # xbmc.log(msg=repr(player.getPlayingItem()), level=xbmc.LOGINFO)

        video_aspect = None
        
        if xbmcaddon.Addon().getSetting("auto_detect_ar") == "false":
            video_aspect = self.manuallySelectVideoAspectRatio()
        else:
            video_aspect = self.getPlayingVideoAspectRatio()
            if video_aspect is None:
                warn("Video Aspect Ratio Not Detected, Manually Select")
                video_aspect = self.manuallySelectVideoAspectRatio()

        zoom_amt = round(video_aspect / standard_screen_aspect, 2)
        pixel_ratio = round(standard_screen_aspect / scope_screen_aspect, 2)

        self.setPlayerViewMode(zoom_amt, pixel_ratio)
        notify("{} video Fit to Screen zoom:{} pixel ratio:{}".format(video_aspect, zoom_amt, pixel_ratio))

    def getPlayingVideoAspectRatio(self):
        playerid = self.getActiveVideoPlayerId()
        req = {'jsonrpc': '2.0',"method": "Player.GetItem",
               "params": {"properties": ["streamdetails"], "playerid": playerid }, 
               "id": "VideoGetItem"
               }
        resp = json.loads(xbmc.executeJSONRPC(json.dumps(req)))

        try:
            for video in resp["result"]["item"]["streamdetails"]["video"]:
                if "aspect" in video:
                    return round(video["aspect"], 2)
        except KeyError:
            return None

    def setPlayerViewMode(self, zoom_amt, pixel_ratio):
        req = {'jsonrpc': '2.0',"method": "Player.SetViewMode",
               "params": {"viewmode": {"zoom": zoom_amt, "pixelratio": pixel_ratio}}, 
               "id": 1
               }
        xbmc.executeJSONRPC(json.dumps(req))

    def getActiveVideoPlayerId(self):
        req = {'jsonrpc': '2.0',"method": "Player.GetActivePlayers",
               "id": 1
                }
        resp = json.loads(xbmc.executeJSONRPC(json.dumps(req)))

        for player in resp["result"]:
            if player["type"] == "video":
                return player["playerid"]

        warn("Active video player not found, skipping adjustment")
        return None

    def manuallySelectVideoAspectRatio(self):
        options = ['2.4', '2.0', '1.85', '1.78', '1.33']
        selected_position = xbmcgui.Dialog().select("Select Video Aspect Ratio", options)
        return float(options[selected_position])
                                                            
    def captureAspectRatio(self):
        xbmc.sleep(500)
        return xbmc.RenderCapture().getAspectRatio()

    def showOriginal(self):
        self.setPlayerViewMode(1.0, 1.0)
        notify("Showing original aspect ratio")

p = Player()

while not monitor.abortRequested():
    # Sleep/wait for abort for 10 seconds
    if monitor.waitForAbort(10):
        # Abort was requested while waiting. We should exit
        break
