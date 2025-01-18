---
title: Houdini Tools
---


## Default Preferences

* Disable Nodes Shapes  
* Use Simple Node Shapes  
* Disable Auto Move Nodes  
* Disable Nodes Animations  
* Set Low Size to Show Ring  
* Show Displayed Node instead of Selected Node  
* Create Tools In Context  
* Set UI to Compact Mode  
* Startup with a specific Desktop  




## On Scene Open 

* Apply the default Desktop
* Set Cooking mode to Manual
* ~~Set view to "Show Display Operator"~~ Not possible yet
* ~~Set view to "Hide other objects"~~ Not possible yet

For making the loading of scenes faster and more stable 



## Network View Improvements

* **Drag and drop files from explorer (abc/usd/usd/usd/obj/fbx/txt/mdd/ass/rs/images):**

* **Propagate display flag to children:**
<video playsinline autoplay muted loop>
  <source src="{{site.baseurl}}/medias/propagate_display.mp4" type="video/mp4">
</video>
<br>

* **Create object merge from clipboard (Ctrl+C Alt+V):**
<video playsinline autoplay muted loop>
  <source src="{{site.baseurl}}/medias/paste_object_merge.mp4" type="video/mp4">
</video>
<br>

* **Alt+click to create Nulls:**
<video playsinline autoplay muted loop>
  <source src="{{site.baseurl}}/medias/create_nulls.mp4" type="video/mp4">
</video>
<br>

* **Connect nodes by height position (Shift+Y):**
<video playsinline autoplay muted loop>
  <source src="{{site.baseurl}}/medias/connect_all_nodes.mp4" type="video/mp4">
</video>
<br>

* **Create Node Previews (experimental):**
<video playsinline autoplay muted loop>
  <source src="{{site.baseurl}}/medias/node_preview.mp4" type="video/mp4">
</video>
<br>

* **Improved Cycle display flag (R):**
<video playsinline autoplay muted loop>
  <source src="{{site.baseurl}}/medias/cycle_display.mp4" type="video/mp4">
</video>



## Shortcuts 

* Paste parameters (Ctrl+Shift+C / Ctrl+Shift+V)
* Change particle types of display (Shift+D)
* Show dependency links (Ctrl+D)
* Toggle cooking mode (F10)
* **Changing viewport background color (Shift+B):**
<video playsinline autoplay muted loop>
  <source src="{{site.baseurl}}/medias/change_viewport_color.mp4" type="video/mp4">
</video>
<br>

Scrub Timeline (K) (Video) 

Network Clipboard - Send selected nodes to another user on the same network

---

# [How to install]

Paste [this script](https://raw.githubusercontent.com/Regnareb/Houdini/refs/tags/v0.3.1/python2.7libs/tools/installer.py) to **Houdini > Window > Python Source Editor > Accept**  

Here is what the script does:
 * Download the [latest release](https://github.com/Regnareb/Houdini/releases/latest/download/Houdini-tools.zip) 
 * Extract its content to the Houdini prefs folder 
 * Modify the file `Houdini-tools/REGNAREB.json`, replace `$REGNAREB` with the path to the folder of the folder `Houdini-tools`  
 * Move the `REGNAREB.json` file in a `packages` folder of your Houdini preferences folder


If everything is working fine, it should show that window on the next start of Houdini:
![]({{site.baseurl}}/medias/first_launch.png)

For more tool preferences, activate the Regnareb shelf and press the Preferences button.  
You can also auto-update the tools by clicking the Update button.

![]({{site.baseurl}}/medias/preferences.png)

### For Developers
You can download the code by doing
```
git clone --recurse-submodules -c core.symlinks=true --remote-submodules https://github.com/Regnareb/Houdini.git
```


# How to uninstall

If you want to uninstall the tools, just delete the file `packages/regnareb.json` in your Houdini preferences 


