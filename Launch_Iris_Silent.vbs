' ================================================================
' IRIS AI — Silent Autonomous Desktop Launcher
' Runs all services completely hidden in background (no CMD terminal window).
' ================================================================

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)

WshShell.CurrentDirectory = ScriptDir
WshShell.Run "cmd /c """ & ScriptDir & "\start_all.bat""", 0, False
