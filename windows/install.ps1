#requires -version 2

if (Test-Path program)
{
    Remove-Item 'program' -Recurse;
}

if (Test-Path env)
{
    Remove-Item 'env' -Recurse;
}


$p = &{py -V} 2>&1
# check if an ErrorRecord was returned
$version = if($p -is [System.Management.Automation.ErrorRecord])
{
    # grab the version string from the error message
    $p.Exception.Message
}
else 
{
    # otherwise return as is
    $p
}
if (-Not $version.StartsWith("Python 3"))
{
    Write-Host 'Install Python from https://www.python.org/downloads/';
    Write-Host 'Press any key to continue...';
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown');
    exit(1)
}

try {
    deactivate
}
catch {
    
}

py -m pip install --upgrade pip
py -m pip install --user virtualenv
py -m venv env
.\env\Scripts\activate

Write-Host 'Downloading Annotations...';
Invoke-WebRequest "https://github.com/ELITR/Annotations/archive/master.zip" -outfile "master.zip"
Expand-Archive -LiteralPath "master.zip" -DestinationPath "program\"
Remove-Item "master.zip"


Write-Host 'Downloading sox...';
Invoke-WebRequest "http://ufallab.ms.mff.cuni.cz/~polak/sox-14.4.2-win32.exe"  -outfile "sox-14.4.2-win32.exe"
Write-Host 'Use the installation wizard to complete the SOX installation.';
Start-Process .\sox-14.4.2-win32.exe -Verb RunAs -Wait
Remove-Item "sox-14.4.2-win32.exe"

pip install -r program/Annotations-master/requirements.txt
deactivate

$p = (pwd).Path
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("Annotations.lnk")
$Shortcut.TargetPath  = "pythonw"
$Shortcut.Arguments = "program\\Annotations-master\\run.py"
$Shortcut.WorkingDirectory = $p
$Shortcut.Save()
exit(0)