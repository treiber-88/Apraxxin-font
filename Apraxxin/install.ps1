# Installs Apraxxin for the current Windows user (no administrator rights needed).
#   (no switch)  font + keyboard app (to READ and TYPE Apraxxin)
#   -FontOnly    font only (to READ Apraxxin)
# Both also set up the files for the Chrome extension.
param([switch]$FontOnly)
$ErrorActionPreference = 'Stop'
$here    = Split-Path -Parent $MyInvocation.MyCommand.Path
$appDir  = Join-Path $env:LOCALAPPDATA 'Apraxxin'
$fontDir = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'

foreach ($f in 'Apraxxin.ttf', 'ApraxxinKeyboard.exe', 'chrome-extension\manifest.json', 'chrome-extension\content.js') {
    if (-not (Test-Path (Join-Path $here $f))) {
        throw "Missing '$f'. Extract the whole Apraxxin zip first, then run the installer from the extracted folder."
    }
}
# Files downloaded from the internet are marked as blocked by Windows; unblock ours.
Get-ChildItem $here -Recurse -File | Unblock-File -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force $appDir, $fontDir | Out-Null
Add-Type -Namespace Apx -Name Native -MemberDefinition @'
[DllImport("gdi32.dll", CharSet = CharSet.Unicode)] public static extern int AddFontResource(string file);
[DllImport("gdi32.dll", CharSet = CharSet.Unicode)] public static extern bool RemoveFontResource(string file);
[DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr SendMessageTimeout(IntPtr h, uint msg, IntPtr w, IntPtr l, uint flags, uint timeout, out IntPtr result);
'@

# 1. Stop the keyboard app if it is running (it is replaced below; full install only).
if (-not $FontOnly) {
    Get-Process ApraxxinKeyboard -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Milliseconds 300
}

# 2. Font file. Each version gets its own file name; older files are kept because
#    programs that are already open may still be using them.
$fontKey = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
$old = (Get-ItemProperty $fontKey -ErrorAction SilentlyContinue).'Apraxxin (TrueType)'
$src = Join-Path $here 'Apraxxin.ttf'
$hash = (Get-FileHash $src -Algorithm SHA256).Hash.Substring(0, 8)
$dst = Join-Path $fontDir "Apraxxin-$hash.ttf"
if ($old -and $old -ne $dst -and (Test-Path $old)) { [Apx.Native]::RemoveFontResource($old) | Out-Null }
if (-not (Test-Path $dst)) { Copy-Item $src $dst }
New-ItemProperty $fontKey -Name 'Apraxxin (TrueType)' -Value $dst -PropertyType String -Force | Out-Null
[Apx.Native]::AddFontResource($dst) | Out-Null
Write-Host "Font installed."

# 3. System-wide link (EUDC font) so Apraxxin characters show inside any font.
$acp = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage').ACP
$backup = Join-Path $appDir 'eudc-backup.txt'
foreach ($cp in @($acp, '1252') | Select-Object -Unique) {
    $k = "HKCU:\EUDC\$cp"
    $prev = (Get-ItemProperty $k -ErrorAction SilentlyContinue).SystemDefaultEUDCFont
    if ($prev -and $prev -notmatch 'Apraxxin' -and -not (Select-String -Path $backup -Pattern "^$cp=" -Quiet -ErrorAction SilentlyContinue)) {
        Add-Content $backup "$cp=$prev"
    }
    New-Item $k -Force | Out-Null
    New-ItemProperty $k -Name SystemDefaultEUDCFont -Value $dst -PropertyType String -Force | Out-Null
}
$r = [IntPtr]::Zero  # tell running programs the font list changed (WM_FONTCHANGE)
[Apx.Native]::SendMessageTimeout([IntPtr]0xffff, 0x001D, [IntPtr]::Zero, [IntPtr]::Zero, 2, 2000, [ref]$r) | Out-Null
Write-Host "Apraxxin linked into Windows' fonts."

# 4. Chrome extension + chart in a permanent folder (Chrome loads the extension from there).
$ext = Join-Path $appDir 'chrome-extension'
New-Item -ItemType Directory -Force $ext | Out-Null
Copy-Item (Join-Path $here 'chrome-extension\*') $ext -Force
Copy-Item (Join-Path $here 'Apraxxin chart.html') $appDir -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $here 'README.md') $appDir -Force -ErrorAction SilentlyContinue

# 5. Keyboard app (full install only).
if (-not $FontOnly) {
    Copy-Item (Join-Path $here 'ApraxxinKeyboard.exe') $appDir -Force
    $exe = Join-Path $appDir 'ApraxxinKeyboard.exe'
    New-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name ApraxxinKeyboard `
        -Value "`"$exe`"" -PropertyType String -Force | Out-Null
    Start-Process $exe
    Write-Host "Keyboard app installed and started (it also starts with Windows)."
    Write-Host "Turn Apraxxin typing on/off with Ctrl+Shift+A or Numpad Enter."
}

try { Set-Clipboard -Value $ext } catch { }
Write-Host ""
Write-Host "=== Using Google Chrome? One more step ==="
Write-Host " 1. In Chrome, go to:  chrome://extensions"
Write-Host " 2. Switch on 'Developer mode' (top right)."
Write-Host " 3. Click 'Load unpacked' and choose this folder (already copied to your clipboard,"
Write-Host "    so you can paste it into the folder box with Ctrl+V):"
Write-Host "      $ext"
Write-Host ""
Write-Host "Done. Restart programs that were already open (or sign out and back in once)"
Write-Host "so they show Apraxxin."
