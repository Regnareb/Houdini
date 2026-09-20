import hou
import common.hou_utils
from lib.pythonlib.constants import *


COLORSCHEMES = {
    hou.viewportColorScheme.Light: "config/3DSceneColors.light",
    hou.viewportColorScheme.Dark: "config/3DSceneColors.dark",
    hou.viewportColorScheme.Grey: "config/3DSceneColors.bw"
    }
if common.hou_utils.get_houdini_version() >= 22:
    COLORSCHEMES[hou.viewportColorScheme.DarkGrey] = "config/3DSceneColors.dg"

DISPLAYPARTICLES = [hou.viewportParticleDisplay.Points, hou.viewportParticleDisplay.Pixels, hou.viewportParticleDisplay.Lines, hou.viewportParticleDisplay.Discs]

IMAGE_FORMATS = ('.pic', '.pic.Z', '.picZ', '.pic.gz', '.picgz', '.rat', '.tbf', '.dsm', '.picnc', '.piclc', '.rgb', '.rgba', '.sgi', '.tif', '.tif3', '.tif16', '.tif32', '.tiff', '.tx', '.yuv', '.pix', '.als', '.cin', '.kdk', '.jpg', '.jpeg', '.exr', '.png', '.psd', '.psb', '.si', '.tga', '.vst', '.vtg', '.rla', '.rla16', '.rlb', '.rlb16', '.bmp', '.hdr', '.ptx', '.ptex', '.ies', '.dds', '.r16', '.r32', '.qtl')
