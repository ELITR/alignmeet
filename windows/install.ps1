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

Write-Host 'Downloading ffmpeg and sox...';
Invoke-WebRequest "http://ufallab.ms.mff.cuni.cz/~polak/elitr/bin.zip"  -outfile "bin.zip"
Expand-Archive -LiteralPath "bin.zip" -DestinationPath "program\"
Remove-Item "bin.zip"

pip install -r program/Annotations-master/requirements.txt
deactivate

$p = (Get-Location).Path
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("Annotations.lnk")
$Shortcut.TargetPath  = "pythonw"
$Shortcut.Arguments = -join($p, "\program\Annotations-master\run.py")
$Shortcut.WorkingDirectory = $p
$Shortcut.Save()
exit(0)