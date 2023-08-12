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
* Set view to "Show Display Operator"  
* Set view to "Hide other objects"

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

* **Connect nodes by height position:**
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

* Paste parameters with Ctrl+Shift+C / Ctrl+Shift+V 
* Change particle types of display
* Show dependency links
* Toggle cooking mode   
* **Changing viewport background color:**
<video playsinline autoplay muted loop>
  <source src="{{site.baseurl}}/medias/change_viewport_color.mp4" type="video/mp4">
</video>
<br>

Scrub Timeline  (Video) 

Network Clipboard - Send selected nodes to another user on the same network

---

# How to install

Download the [latest release](https://github.com/Regnareb/Houdini/releases) and extract its content.
Modify the file `Houdini-tools/REGNAREB.json`, replace `path/to/this/folder` with the path to the folder of `Houdini-tools`  
Then copy this .json file in your Houdini preference folder, in a `packages` folder   
If everything is working fine, it should show that window on the next start of Houdini:

![]({{site.baseurl}}/medias/first_launch.png)

For more tool preferences, activate the Regnareb shelf and press the Preferences button:

![]({{site.baseurl}}/medias/preferences.png)


# How to uninstall

If you want to uninstall the tools, just delete the file packages/regnareb.json in your Houdini preferences 


