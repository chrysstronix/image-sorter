on run
	set appPath to POSIX path of (path to me)
	set launcherPath to appPath & "Contents/MacOS/launch"
	do shell script "/bin/sh " & quoted form of launcherPath
end run
