#requires -version 2

<# Write-Host 'Updating installation script...'
$tmp = [System.IO.Path]::GetTempFileName()
Invoke-WebRequest "http://ufallab.ms.mff.cuni.cz/~polak/elitr/install.ps1" -outfile installation_updated.ps1

if (Compare-Object -ReferenceObject (Get-Content -Path install.ps1) -DifferenceObject (Get-Content -Path installation_updated.ps1)) {
    Write-Host 'Installation script updated'
    Write-Host 'Repeat the installation with installation_updated.ps1'
    Write-Host 'Press any key to continue...';
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown');
    exit(0)
}
Remove-Item 'installation_updated.ps1'
Write-Host 'Installation script up-to-date' #>

if (Test-Path program) {
    Remove-Item 'program' -Recurse;
}

if (Test-Path env) {
    Remove-Item 'env' -Recurse;
}

Write-Host 'Downloading Annotations...';
Invoke-WebRequest "https://github.com/ELITR/minuting-annotation-tool/archive/master.zip" -outfile "master.zip"
Expand-Archive -LiteralPath "master.zip" -DestinationPath "program\"
Remove-Item "master.zip"

$p = & { py -V } 2>&1
$version = if ($p -is [System.Management.Automation.ErrorRecord]) {
    $p.Exception.Message
}
else {
    $p
}
if (-Not $version.StartsWith("Python 3")) {
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

Write-Host 'Do you wish to create a new virtual python enviroment? [y/n] (Default: "n", if you don''t know just type "n" and press Enter key):'
$venv = Read-Host

if ($venv -Eq 'y') {
    py -m pip install --user virtualenv
    py -m venv env
    .\env\Scripts\activate
    pip install -r program/minuting-annotation-tool-master/requirements.txt
    deactivate
}
else {
    py -m pip install --user -r program/minuting-annotation-tool-master/requirements.txt
}

$arch = py -c "import struct
print(struct.calcsize('P') * 8)"

if (($arch -Gt 32 -And -Not (Test-Path "C:\Program Files\VideoLAN\VLC")) -Or
    ($arch -Lt 64 -And -Not (Test-Path "C:\Program Files (x86)\VideoLAN\VLC"))) {
    Write-Host 'Downloading VLC...';
    if ($arch -Gt 32) {
        Invoke-WebRequest "http://ufallab.ms.mff.cuni.cz/~polak/elitr/vlc-3.0.9.2-win64.zip"  -outfile "vlc.zip"
    }
    else {
        Invoke-WebRequest "http://ufallab.ms.mff.cuni.cz/~polak/elitr/vlc-3.0.9.2-win32.zip"  -outfile "vlc.zip"
    }
    Expand-Archive -LiteralPath "vlc.zip" -DestinationPath "program\"
    Remove-Item "vlc.zip"
}

Invoke-WebRequest "http://ufallab.ms.mff.cuni.cz/~polak/elitr/run.ps1" -outfile run.ps1

$p = (Get-Location).Path
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("Annotations.lnk")
if ($venv -Eq 'y') {
    $Shortcut.TargetPath = -join ($p, "\env\Scripts\pythonw")
}
else {
    $Shortcut.TargetPath = "pythonw"
}
$Shortcut.Arguments = -join ($p, "\program\minuting-annotation-tool-master\run.py")
$Shortcut.WorkingDirectory = $p
$Shortcut.Save()

Write-Host 'Installation finished, press any key to continue...';
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown');

exit(0)