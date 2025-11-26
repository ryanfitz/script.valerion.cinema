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
        self.current_zoom_amt = None

    def onAVStarted(self):
        if not player.isPlayingVideo:
            return

        scope_screen_aspect = float(xbmcaddon.Addon().getSetting("screen_ar"))
        standard_screen_aspect = 16/9

        # xbmc.log(msg=repr(player.getPlayingItem()), level=xbmc.LOGINFO)

        video_aspect = None
        container_aspect = float(xbmc.getInfoLabel("Player.Process(VideoDAR)"))

        # Check for DoVi L5 offsets first
        dovi_aspect = self.getDoViAspectRatio()
        if dovi_aspect:
            video_aspect = dovi_aspect
        else:
            video_stream_details = self.getPlayingVideoStreamDetails()
            if video_stream_details is not None:
                video_aspect = video_stream_details.get('video_ar')
        
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

    def getDoViAspectRatio(self):
        dovi_top = xbmc.getInfoLabel("Player.Process(video.dovi.l5.top.offset)")
        if dovi_top:
            try:
                top = int(dovi_top)
                bottom = int(xbmc.getInfoLabel("Player.Process(video.dovi.l5.bottom.offset)") or 0)
                left = int(xbmc.getInfoLabel("Player.Process(video.dovi.l5.left.offset)") or 0)
                right = int(xbmc.getInfoLabel("Player.Process(video.dovi.l5.right.offset)") or 0)
                
                width = int(xbmc.getInfoLabel("Player.Process(VideoWidth)") or 0)
                height = int(xbmc.getInfoLabel("Player.Process(VideoHeight)") or 0)
                
                if width > 0 and height > 0:
                    active_width = width - left - right
                    active_height = height - top - bottom
                    if active_height > 0:
                        video_aspect = round(float(active_width) / float(active_height), 2)
                        xbmc.log("Valerion Cinema: Using DoVi L5 offsets - AR: {}".format(video_aspect), level=xbmc.LOGINFO)
                        return video_aspect
            except ValueError:
                xbmc.log("Valerion Cinema: Failed to parse DoVi L5 offsets", level=xbmc.LOGERROR)
        return None

    def setDoViViewMode(self):
        dovi_aspect = self.getDoViAspectRatio()
        if dovi_aspect:
            scope_screen_aspect = float(xbmcaddon.Addon().getSetting("screen_ar"))
            standard_screen_aspect = 16/9
            container_aspect = float(xbmc.getInfoLabel("Player.Process(VideoDAR)"))
            
            if dovi_aspect >= container_aspect:
                zoom_amt = round(dovi_aspect / container_aspect, 2)
            else:
                zoom_amt = 1.0

            pixel_ratio = round(standard_screen_aspect / scope_screen_aspect, 2)

            self.setPlayerViewMode(zoom_amt, pixel_ratio)
            notify("{} Video Fit to {} Screen\nzoom:{} pixel ratio:{}".format(dovi_aspect, scope_screen_aspect, zoom_amt, pixel_ratio))

    def setPlayerViewMode(self, zoom_amt, pixel_ratio):
        if zoom_amt != self.current_zoom_amt:
            req = {'jsonrpc': '2.0',"method": "Player.SetViewMode",
                   "params": {"viewmode": {"zoom": zoom_amt, "pixelratio": pixel_ratio}}, 
                   "id": 1
                   }
            result_raw = xbmc.executeJSONRPC(json.dumps(req))
            result = json.loads(result_raw)
            if result["result"] != "OK":
                xbmc.log("Valerion Cinema: Failed to set view mode", level=xbmc.LOGERROR)
            else:
                self.current_zoom_amt = zoom_amt
                xbmc.log("Valerion Cinema: Set view mode to zoom:{} pixel ratio:{}".format(zoom_amt, pixel_ratio), level=xbmc.LOGINFO)

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
