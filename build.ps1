# List of libraries to include
$librarys = @("ttkbootstrap", "chlorophyll")

function Get-LibraryPath {
    param(
        [string]$library
    )

    $pip_show_output = & pip show $library
    $library_path = ""

    foreach ($line in $pip_show_output) {
        if ($line -like "Location: *") {
            $library_path = $line -replace "Location: ", ""
            break
        }
    }

    return $library_path
}

$psScriptRoot = $PSScriptRoot
$icon_path = Join-Path $psScriptRoot "software.ico"
$internal_path = Join-Path $psScriptRoot "_internal"
$plugins_path = Join-Path $psScriptRoot "plugins"
$py_script_path = Join-Path $psScriptRoot "Organizer_win.py"

$pyinstallerCmd = "pyinstaller --noconfirm --onedir --windowed --distpath Organizer --icon `"$icon_path`" --add-data `"$icon_path;.`" --add-data `"$internal_path;_internal/`" --add-data `"$plugins_path;plugins/`""

foreach ($library in $librarys) {
    $library_path = Get-LibraryPath -library $library

    if ($library_path) {
        Write-Host "Library Path for '$library' is: $library_path" -ForegroundColor White
        $pyinstallerCmd += " --add-data `"$library_path\$library;$library/`""
    } else {
        Write-Host "Library Path not found for '$library'" -ForegroundColor Red
    }
}

$pyinstallerCmd += " `"$py_script_path`""

Write-Host "Building Organizer.exe..." -ForegroundColor Blue
Invoke-Expression $pyinstallerCmd
Write-Host "Organizer.exe build complete" -ForegroundColor Green