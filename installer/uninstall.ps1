# Removes Apraxxin for the current Windows user and restores previous EUDC settings.
$ErrorActionPreference = 'Continue'
$appDir = Join-Path $env:LOCALAPPDATA 'Apraxxin'
Add-Type -Namespace Apx -Name Native -MemberDefinition @'
[DllImport("gdi32.dll", CharSet = CharSet.Unicode)] public static extern bool RemoveFontResource(string file);
'@

Get-Process ApraxxinKeyboard -ErrorAction SilentlyContinue | Stop-Process -Force
Remove-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name ApraxxinKeyboard -ErrorAction SilentlyContinue

# EUDC links: restore what was there before, or remove ours.
$backup = Join-Path $appDir 'eudc-backup.txt'
$saved = @{}
if (Test-Path $backup) { Get-Content $backup | ForEach-Object { $p = $_ -split '=', 2; $saved[$p[0]] = $p[1] } }
Get-ChildItem 'HKCU:\EUDC' -ErrorAction SilentlyContinue | ForEach-Object {
    $v = (Get-ItemProperty $_.PSPath).SystemDefaultEUDCFont
    if ($v -match 'Apraxxin') {
        $cp = $_.PSChildName
        if ($saved.ContainsKey($cp)) { Set-ItemProperty $_.PSPath -Name SystemDefaultEUDCFont -Value $saved[$cp] }
        else { Remove-ItemProperty $_.PSPath -Name SystemDefaultEUDCFont }
    }
}

# Font.
$fontKey = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
$f = (Get-ItemProperty $fontKey -ErrorAction SilentlyContinue).'Apraxxin (TrueType)'
if ($f) {
    [Apx.Native]::RemoveFontResource($f) | Out-Null
    Remove-ItemProperty $fontKey -Name 'Apraxxin (TrueType)'
    Remove-Item $f -ErrorAction SilentlyContinue
}
# older versions kept by updates
Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts') -Filter 'Apraxxin*.ttf' -ErrorAction SilentlyContinue |
    Remove-Item -ErrorAction SilentlyContinue
Remove-Item $appDir -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Apraxxin removed. (Remove the Chrome extension from chrome://extensions if you added it.)"
