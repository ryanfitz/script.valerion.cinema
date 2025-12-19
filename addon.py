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
    xbmc.log("Valerion Cinema: {}".format(msg), level=xbmc.LOGINFO)
    xbmcgui.Dialog().notification("Valerion Cinema", msg, __icon__, 5000)

def warn(msg):
    xbmc.log("Valerion Cinema: {}".format(msg), level=xbmc.LOGWARNING)
    xbmcgui.Dialog().notification("Valerion Cinema", msg, xbmcgui.NOTIFICATION_WARNING, 5000)

class Player(xbmc.Player):
    def __init__(self):
        xbmc.Player.__init__(self)
        self.current_zoom_amt = None
        self.current_pixel_ratio = None
        self.video_stream_details = None

    def onAVStarted(self):
        # reset zoom and pixel ratio on new video
        self.current_zoom_amt = None
        self.current_pixel_ratio = None
        self.video_stream_details = None

        if not player.isPlayingVideo():
            return

        scope_screen_aspect = float(xbmcaddon.Addon().getSetting("screen_ar"))
        standard_screen_aspect = 16/9

        self.video_stream_details = self.getPlayingVideoStreamDetails()
        # xbmc.log(msg=repr(player.getPlayingItem()), level=xbmc.LOGINFO)

        video_aspect = None
        container_aspect = float(xbmc.getInfoLabel("Player.Process(VideoDAR)"))

        aspect_source = "unknown"
        # Check for DoVi L5 offsets first
        dovi_aspect = self.getDoViAspectRatio()
        if dovi_aspect is not None:
            video_aspect = dovi_aspect
            aspect_source = "DoVi"
        elif self.video_stream_details is not None:
            video_aspect = self.video_stream_details.get('video_ar')
            aspect_source = "NFO"
        
        if xbmcaddon.Addon().getSetting("auto_detect_ar") == "false":
            video_aspect = self.manuallySelectVideoAspectRatio()
            aspect_source = "Manual"
        elif video_aspect is None:
            warn("Video Aspect Ratio Not Detected, Manually Select")
            video_aspect = self.manuallySelectVideoAspectRatio()
            aspect_source = "Manual"

        # only zoom videos wider than container
        if video_aspect >= container_aspect:
            zoom_amt = round(video_aspect / container_aspect, 2)
        else:
            zoom_amt = 1.0

        pixel_ratio = round(standard_screen_aspect / scope_screen_aspect, 2)

        self.setPlayerViewMode(zoom_amt, pixel_ratio, aspect_source)
        notify("{} Video Fit to {} Screen\n{} zoom:{} pixel ratio:{}".format(video_aspect, scope_screen_aspect, aspect_source, zoom_amt, pixel_ratio))

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

    def is_valid_infolabel(self, label, value):
        return value and value.strip() and value.lower() != label.lower()
    
    def getInfoLabelInt(self, label):
        return int(xbmc.getInfoLabel(label).replace(",", "") or 0)

    def getDoViAspectRatio(self):
        offset_top_label = 'Player.Process(video.dovi.l5.top.offset)'
        dovi_top = xbmc.getInfoLabel(offset_top_label)

        if self.is_valid_infolabel(offset_top_label, dovi_top):
            try:
                top = int(dovi_top.replace(",", ""))
                bottom = self.getInfoLabelInt('Player.Process(video.dovi.l5.bottom.offset)')
                left = self.getInfoLabelInt('Player.Process(video.dovi.l5.left.offset)')
                right = self.getInfoLabelInt('Player.Process(video.dovi.l5.right.offset)')
                xbmc.log("Valerion Cinema: DoVi L5 offsets top: {} bottom: {} left: {} right: {}".format(top, bottom, left, right), level=xbmc.LOGINFO)

                width = self.getInfoLabelInt('Player.Process(VideoWidth)')
                height = self.getInfoLabelInt('Player.Process(VideoHeight)')
                
                if width > 0 and height > 0:
                    active_width = width - left - right
                    active_height = height - top - bottom
                    if active_height > 0:
                        video_aspect = round(float(active_width) / float(active_height), 2)
                        # xbmc.log("Valerion Cinema: Using DoVi L5 offsets - AR: {}".format(video_aspect), level=xbmc.LOGINFO)
                        return video_aspect
            except ValueError as e:
                xbmc.log("Valerion Cinema: Failed to parse DoVi L5 offsets {}".format(e), level=xbmc.LOGERROR)
        return None

    def setViewModeUsingDoViOffsets(self):
        dovi_aspect = self.getDoViAspectRatio()
        if dovi_aspect is not None:
            scope_screen_aspect = float(xbmcaddon.Addon().getSetting("screen_ar"))
            standard_screen_aspect = 16/9
            container_aspect = float(xbmc.getInfoLabel("Player.Process(VideoDAR)"))
            
            if dovi_aspect >= container_aspect:
                zoom_amt = round(dovi_aspect / container_aspect, 2)
            else:
                zoom_amt = 1.0

            pixel_ratio = round(standard_screen_aspect / scope_screen_aspect, 2)

            self.setPlayerViewMode(zoom_amt, pixel_ratio, "DoVi")

    def setPlayerViewMode(self, zoom_amt, pixel_ratio, aspect_source):
        # xbmc.log("Valerion Cinema: attempting to set view mode to zoom:{} pixel ratio:{}".format(zoom_amt, pixel_ratio), level=xbmc.LOGINFO)
        if zoom_amt != self.current_zoom_amt or pixel_ratio != self.current_pixel_ratio:
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
                self.current_pixel_ratio = pixel_ratio
                xbmc.log("Valerion Cinema: {} Set view mode to zoom:{} pixel ratio:{}".format(aspect_source, zoom_amt, pixel_ratio), level=xbmc.LOGINFO)

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
    if player.isPlayingVideo():
        p.setViewModeUsingDoViOffsets()

    # Sleep/wait for abort for 10 seconds
    if monitor.waitForAbort(0.1):
        # Abort was requested while waiting. We should exit
        break
