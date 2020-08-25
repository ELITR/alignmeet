if (Test-Path program)
{
    Remove-Item 'program' -Recurse;
}

$v = python3 -V;
if (-Not $v.StartsWith("Python 3"))
{
    Write-Host -NoNewLine 'Press any key to continue...';
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown');
    exit(1)
}

py -m pip install --upgrade pip
py -m pip install --user virtualenv
py -m venv env
.\env\Scripts\activate

wget "https://github.com/ELITR/Annotations/archive/master.zip" -outfile "master.zip"
Expand-Archive -LiteralPath "master.zip" -DestinationPath "program\"
Remove-Item "master.zip"

pip install -r program/requirements.txt
deactivate