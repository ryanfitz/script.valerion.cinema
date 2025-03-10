# Valerion Cinema Kodi Addon
Scope Screen Support for Valerion Projectors. This kodi addon will automatically fit videos to a scope screen, minimizing blackbars and maintaing correct aspect ratio. 

***Addon requires that your valerion projector is in ultrawide mode, which is enabled by using valerion's auto screen alignment.***

![](https://raw.githubusercontent.com/ryanfitz/script.valerion.cinema/refs/heads/main/resources/screenshot-1.jpg)

## Setup
1. Download install zip file from [releases](https://github.com/ryanfitz/script.valerion.cinema/releases)
2. Launch Kodi >> Add-ons >> Get More >> Install from zip file
3. Configure your screen aspect ratio: 
  - Go to Add-ons >> My add-ons >> Valerion Cinema >> Configure >> Screen Aspect Ratio

![](https://raw.githubusercontent.com/ryanfitz/script.valerion.cinema/refs/heads/main/resources/screenshot-2.jpg)


## How it Works
When playing a video this addon will attempt to detect the video's aspect ratio. If this fails, it will fallback to prompting for the aspect ratio. 

With the video aspect ratio set, the addon will auto correct the video's pixel ratio to correct for valerions ultrawide presentation, and zoom to fill the height of your screen.

This will maintain correct aspect ratio, and fill the entire height of a scope screen, for automatic CIH presentation. Black bars will only be present on left and right sides of screen when playing a non-scope video.