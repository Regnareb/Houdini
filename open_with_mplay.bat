start /min "OpenMPLAY" "python" %~dp0open_with_mplay.py %1 

if NOT ["%errorlevel%"]==["0"] pause 
