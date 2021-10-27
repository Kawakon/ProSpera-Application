@echo off
SET _wd=%cd%
echo %_wd%
SET result=%_wd:~9%
for /f "delims=\" %%i in ("%result%") do (set user=%%i)
echo %user%
IF not exist "C:\Users\%user%\Desktop\ProSpera Camera Test.lnk" (powershell "$current=Get-Location -PSDrive C; echo $current; cd $home/Desktop; $sourceFile='ProSpera Camera Test.lnk'; $s=(New-Object -ComObject WScript.Shell); $shortcut=$s.CreateShortcut($sourceFile); $shortcut.TargetPath='%_wd%\dist\ProSpera Camera Test.exe'; echo $shortcut.TargetPath; $shortcut.IconLocation='%_wd%\valley.ico'; $shortcut.Save(); cd $current; Move-Item '.\ProSpera Camera Test.lnk' -Destination $home\Desktop")
IF exist "C:\Program Files (x86)\Nmap" ("./dist/ProSpera Camera Test.exe") ELSE (nmap-7.91-setup.exe && powershell "$env:Path=([System.Environment]::GetEnvironmentVariable('Path','Machine'),[System.Environment]::GetEnvironmentVariable('Path','User')) -match '.' -join ';'; echo $env:Path; Start-Process -FilePath './dist/ProSpera Camera Test.exe'" || echo "Error while installing Nmap...")
