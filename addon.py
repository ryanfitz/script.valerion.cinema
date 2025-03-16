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
    xbmcgui.Dialog().notification("Valerion Cinema", msg, __icon__, 5000)

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
        container_aspect = standard_screen_aspect 

        video_stream_details = self.getPlayingVideoStreamDetails()
        if video_stream_details is not None:
            video_aspect = video_stream_details.get('video_ar')
            container_aspect = video_stream_details.get('container_ar')
        
        if xbmcaddon.Addon().getSetting("auto_detect_ar") == "false":
            video_aspect = self.manuallySelectVideoAspectRatio()
        elif video_aspect is None:
            warn("Video Aspect Ratio Not Detected, Manually Select")
            video_aspect = self.manuallySelectVideoAspectRatio()

        # only zoom videos wider than container
        if video_aspect >= container_aspect:
            zoom_amt = round(video_aspect / container_aspect, 2)
        else:
            zoom_amt = 1.0

        pixel_ratio = round(standard_screen_aspect / scope_screen_aspect, 2)

        self.setPlayerViewMode(zoom_amt, pixel_ratio)
        notify("{} Video Fit to {} Screen\nzoom:{} pixel ratio:{}".format(video_aspect, scope_screen_aspect, zoom_amt, pixel_ratio))

    def getPlayingVideoStreamDetails(self):
        playerid = self.getActiveVideoPlayerId()
        req = {'jsonrpc': '2.0',"method": "Player.GetItem",
               "params": {"properties": ["streamdetails"], "playerid": playerid }, 
               "id": "VideoGetItem"
               }
        resp = json.loads(xbmc.executeJSONRPC(json.dumps(req)))

        try:
            result = {}
            for video in resp["result"]["item"]["streamdetails"]["video"]:
                if "aspect" in video:
                    result["video_ar"] = round(video["aspect"], 2)
                if "height" in video and "width" in video:
                    result["container_ar"] = round(video["width"] / video["height"], 2)
        
            return result
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
