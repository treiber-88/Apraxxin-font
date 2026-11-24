# Apraxxin

Apraxxin is a handwritten alphabet. This package lets you **read** Apraxxin
text on your computer and, if you want, **type** it in any program.

**Works on:** Windows 10 and Windows 11.
**Does not work on:** phones, tablets, Macs, or Linux. Those devices will
show Apraxxin text as empty boxes, and there is no way to fix that there.

---

## 1. Install

1. **Extract the zip first.** Right-click `Apraxxin.zip` → **Extract All…** →
   **Extract**. (Running the installer from inside the zip will not work.)
2. Open the extracted `Apraxxin` folder and double-click one of these:

   | File | Choose it if you want to… |
   |---|---|
   | **Install Apraxxin.cmd** | read *and* type Apraxxin |
   | **Install font only (to read Apraxxin).cmd** | only read Apraxxin that other people send you |

3. If a blue **"Windows protected your PC"** box appears, click
   **More info** → **Run anyway**. Windows shows this for any program that
   isn't from a big company; Apraxxin doesn't need administrator rights and
   only installs for your own Windows account.
4. A black window lists what was installed. Press any key to close it.
5. **Restart programs that were already open** (or sign out of Windows and
   back in once) so they pick up the new font.

## 2. Google Chrome: add the extension

Chrome doesn't use Windows' font settings for special characters, so it needs
a small extension. (Microsoft Edge does **not** need this; it works right away.)

1. Open Chrome and type this into the address bar, then press Enter:

   ```
   chrome://extensions
   ```

2. Switch on **Developer mode** (the switch in the top-right corner).
3. Click **Load unpacked** (top-left).
4. In the folder window, paste this into the address bar and press Enter
   (the installer already copied it to your clipboard, so **Ctrl+V** works):

   ```
   %LOCALAPPDATA%\Apraxxin\chrome-extension
   ```

   Then click **Select Folder**.
5. **Apraxxin for Chrome** now appears in the list. Reload any open tabs.

Notes:
- Keep Developer mode switched on; Chrome may remind you about developer
  extensions now and then. That's normal; click to keep it.
- The extension only adds the Apraxxin font to web pages. It doesn't read or
  send anything.

## 3. Typing Apraxxin (full install only)

- Press **Ctrl+Shift+A** (or the **Enter key on the number pad**) to switch
  Apraxxin typing **on**. A small notice appears at the bottom-right of the
  screen. Press it again to switch back to normal typing.
- You can also click the round Apraxxin icon near the clock (it may be hidden
  behind the **^** arrow). Right-click it for more options.
- **Shift** or **Caps Lock** gives capital letters (they have a line above them).
- **Shift + -** types the long dash. Quotes `"` and `'` pick the opening or
  closing shape automatically.
- Keys without an Apraxxin version (`@ # $ % ^ < > | ~`) type normally, and
  shortcuts like Ctrl+C / Ctrl+V still work.
- `Apraxxin chart.html` shows every character, with a box to try it out.

## Where Apraxxin shows up

| Program | Shows Apraxxin? |
|---|---|
| Microsoft Edge, Notepad, Word, most Windows programs | Yes |
| Google Chrome (Google Docs, Facebook, Discord in the browser, …) | Yes, after step 2 |
| VS Code | Add `Apraxxin` to the end of the **Editor: Font Family** setting |
| Discord desktop app | No. Use Discord in Chrome or Edge instead |
| Firefox | No |

**Important:** the person you message only sees Apraxxin if *they* have
installed it too. Everyone else sees boxes, so send them this package.

## Something's not working?

- **Boxes instead of Apraxxin:** restart that program, or sign out of Windows
  and back in. In Chrome, check the extension is switched on.
- **Typing comes out normal:** make sure the Apraxxin icon near the clock is
  yellow (on). If it isn't there, run **Install Apraxxin.cmd** again.
- **Typing doesn't work in one particular program:** Windows doesn't let
  normal programs type into programs running "as administrator".
- **Antivirus warning:** the typing tool watches your key presses to swap
  letters, which some antivirus programs find suspicious. It stores and
  sends nothing.

## Uninstall

Double-click **Uninstall Apraxxin.cmd**, then remove **Apraxxin for Chrome**
from `chrome://extensions` if you added it.
