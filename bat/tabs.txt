@echo off
REM Opens 6 Chrome incognito windows across the TOP HALF of a 4K (3840x2160) screen

set "URL=http://demo.aviatrix.bet/?sd=cricket&prod&demo=true&lang=en&js"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"& {
    # Try common Chrome paths, fallback to 'chrome' in PATH
    $chromePaths = @(
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        'chrome'
    )
    $chrome = $chromePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $chrome) { $chrome = 'chrome' }

    $url = '%URL%'

    # Fixed 4K screen geometry
    $screenW = 3840
    $screenH = 2160

    # Top half only
    $cols = 6
    $rowHeight = [math]::Floor($screenH / 2)    # 1080
    $winWidth = [math]::Floor($screenW / $cols) - 8   # small padding
    $winHeight = $rowHeight - 8

    # Launch 6 windows side-by-side at the top
    for ($i = 0; $i -lt 6; $i++) {
        $x = $i * [math]::Floor($screenW / $cols) + 4
        $y = 4
        $args = @(
            '--new-window',
            '--incognito',
            \"--window-position=$x,$y\",
            \"--window-size=$winWidth,$winHeight\",
            $url
        )
        Start-Process -FilePath $chrome -ArgumentList $args
        Start-Sleep -Milliseconds 250
    }
    exit 0
}"

exit /b 0
