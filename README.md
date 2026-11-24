# Apraxxin

Type in the Apraxxin script anywhere on Windows.

## Using it
- **Ctrl+Shift+A** or **Numpad Enter** turns Apraxxin typing on/off (or left-click the tray icon). Note: this takes over Ctrl+Shift+A in other programs. A small notice appears at the bottom right.
- Shift / Caps Lock give capitals (glyph with a line above). `"` and `'` choose opening/closing forms automatically. **Shift + -** types the em dash.
- Keys without an Apraxxin character (`@ # $ % ^ < > | ~`) type normally. Ctrl/Alt shortcuts are not affected.
- Tray menu: convert clipboard text to/from Apraxxin, start with Windows, exit.
- `Apraxxin/Apraxxin chart.html`: a chart of every character with a try-it box.

## Where it shows up
| App | How |
|---|---|
| Edge, Notepad, Word, most Windows programs | System EUDC font link, automatic (restart open programs; older programs may need a sign-out/in once) |
| Chrome (Google Docs, Facebook, Discord web) | Load `%LOCALAPPDATA%\Apraxxin\chrome-extension` in chrome://extensions (Developer mode → Load unpacked) |
| VS Code | `Apraxxin` added to `editor.fontFamily` / `terminal.integrated.fontFamily` |
| Discord desktop app | Not supported (it ignores the system link and allows no custom fonts). Use Discord in Edge or Chrome. |

Other people see Apraxxin only if they install it too. **Send them `Apraxxin.zip`** (rebuilt by `tools/release.py`); its `README.md` walks them through installing (read-only or read+type) and adding the Chrome extension. Windows 10/11 only; no runtime needed (the keyboard app targets .NET Framework 4.8).

## How it works / editing glyphs
- Characters are Unicode Private Use Area code points: `U+E000 + ASCII code` (e.g. `a` → U+E061), plus U+E080 (closing ”) and U+E081 (em dash).
- `glyphs.py`: every glyph drawn as straight strokes (and a few curves) in font units (baseline 0, cap height 700), traced from the photos.
- `python tools/preview.py <keys>`: overlays the drawing on the photo → `build/preview/sel_*.png` (`ZOOM=0.8` for a closer look).
- `python tools/build_font.py`: builds `build/Apraxxin.ttf` (placement/size rules in `PLACE`).
- `python tools/release.py`: rebuilds the font and keyboard app and fills the `Apraxxin/` folder; then run `Apraxxin/Install Apraxxin.cmd`.
- `keyboard/`: the C# tray app (`ApraxxinKeyboard.exe --selftest <report.txt>` runs an automated typing test).
- `chrome-extension/`: adds Apraxxin as a Private-Use-only fallback face to each font family a page uses.
- `tools/sources.py`: where each character is in the photos (`tools/prep.py` makes the upright copies in `source/`, `tools/showboxes.py` draws the boxes).
