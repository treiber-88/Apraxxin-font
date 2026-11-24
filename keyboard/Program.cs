// Apraxxin Keyboard: type in the Apraxxin script anywhere in Windows.
//
// Numpad Enter toggles Apraxxin typing on/off (also: click the tray icon).
// While on, letters, digits and the supported punctuation are replaced by the
// Apraxxin characters (Unicode Private Use Area U+E000 + ASCII code), which every
// app displays through the Apraxxin EUDC font link set up by Install.cmd.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Diagnostics;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.Runtime.InteropServices;
using Microsoft.Win32;

namespace ApraxxinKeyboard;

static class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        using var mutex = new Mutex(true, @"Local\ApraxxinKeyboard", out bool first);
        if (!first) return; // already running
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        if (args.Length >= 2 && args[0] == "--selftest") { Environment.ExitCode = SelfTest.Run(args[1]); return; }
        Application.Run(new TrayApp(args.Contains("--on")));
    }
}

/// <summary>Character mapping between ordinary text and Apraxxin code points.</summary>
public static class Apraxxin
{
    public const int Pua = 0xE000;
    public const char CloseDoubleQuote = '\uE080';
    public const char EmDash = '\uE081';
    public const char WideSpace = '\u2002'; // en space: wider than a normal space, still wraps
    const string Direct = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:;,/\\+-=!.?&*()[]{}";

    public static bool IsDirect(char c) => Direct.IndexOf(c) >= 0;

    /// <summary>Converts a typed character; prev is the character before it (for smart quotes).</summary>
    public static char? Convert(char c, char prev)
    {
        if (IsDirect(c)) return (char)(Pua + c);
        bool opening = prev == '\0' || char.IsWhiteSpace(prev) || "([{\uE028\uE05B\uE07B\uE022\uE060".IndexOf(prev) >= 0;
        return c switch
        {
            '"' => opening ? (char)(Pua + '"') : CloseDoubleQuote,
            '\'' => opening ? (char)(Pua + '`') : (char)(Pua + '\''),
            '`' => (char)(Pua + '`'),
            '_' => EmDash,
            ' ' => WideSpace,
            _ => null,
        };
    }

    public static string ToApraxxin(string s)
    {
        var sb = new System.Text.StringBuilder(s.Length);
        char prev = '\0';
        foreach (char c in s)
        {
            char? m = c switch
            {
                '\u201C' => (char)(Pua + '"'), '\u201D' => CloseDoubleQuote,
                '\u2018' => (char)(Pua + '`'), '\u2019' => (char)(Pua + '\''),
                '\u2014' or '\u2013' => EmDash,
                _ => Convert(c, prev),
            };
            sb.Append(m ?? c);
            prev = c;
        }
        return sb.ToString();
    }

    public static string FromApraxxin(string s)
    {
        var sb = new System.Text.StringBuilder(s.Length);
        foreach (char c in s)
        {
            if (c == CloseDoubleQuote) sb.Append('"');
            else if (c == EmDash) sb.Append('\u2014');
            else if (c == WideSpace) sb.Append(' ');
            else if (c > Pua && c < Pua + 0x80) { char a = (char)(c - Pua); sb.Append(a == '`' ? '\'' : a); }
            else sb.Append(c);
        }
        return sb.ToString();
    }
}

sealed class TrayApp : ApplicationContext
{
    readonly NotifyIcon tray;
    readonly ToolStripMenuItem toggleItem, startupItem;
    readonly KeyboardHook hook;
    readonly Icon iconOn, iconOff;
    readonly Toast toast;
    readonly FontFamily? apraxxinFamily;
    readonly PrivateFontCollection fonts = new();

    const string RunKey = @"Software\Microsoft\Windows\CurrentVersion\Run";
    const string RunName = "ApraxxinKeyboard";

    public void Shutdown() => ExitThreadCore();

    public TrayApp(bool startOn, bool acceptInjected = false)
    {
        apraxxinFamily = LoadEmbeddedFont();
        iconOn = MakeIcon(true);
        iconOff = MakeIcon(false);
        toast = new Toast(apraxxinFamily);

        toggleItem = new ToolStripMenuItem("Type in Apraxxin  (Numpad Enter or Ctrl+Shift+A)", null, (_, _) => Toggle());
        startupItem = new ToolStripMenuItem("Start with Windows", null, (_, _) => SetStartup(!startupItem!.Checked))
        { Checked = IsStartupEnabled() };
        var menu = new ContextMenuStrip();
        menu.Items.Add(toggleItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add("Convert clipboard text to Apraxxin", null, (_, _) => ConvertClipboard(true));
        menu.Items.Add("Convert clipboard text back to English letters", null, (_, _) => ConvertClipboard(false));
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(startupItem);
        menu.Items.Add("Exit", null, (_, _) => ExitThread());

        tray = new NotifyIcon { ContextMenuStrip = menu, Visible = true };
        tray.MouseClick += (_, e) => { if (e.Button == MouseButtons.Left) Toggle(); };

        hook = new KeyboardHook { AcceptInjected = acceptInjected };
        hook.Toggled += () => SetEnabled(hook.Enabled, showToast: true);
        hook.Install();
        SetEnabled(startOn, showToast: false);
    }

    void Toggle() => SetEnabled(!hook.Enabled, showToast: true);

    void SetEnabled(bool on, bool showToast)
    {
        hook.Enabled = on;
        toggleItem.Checked = on;
        tray.Icon = on ? iconOn : iconOff;
        tray.Text = on ? "Apraxxin typing: ON (Ctrl+Shift+A or Numpad Enter to turn off)" : "Apraxxin typing: OFF (Ctrl+Shift+A or Numpad Enter to turn on)";
        if (showToast) toast.ShowState(on);
    }

    void ConvertClipboard(bool toApraxxin)
    {
        try
        {
            if (!Clipboard.ContainsText()) return;
            string t = Clipboard.GetText();
            Clipboard.SetText(toApraxxin ? Apraxxin.ToApraxxin(t) : Apraxxin.FromApraxxin(t));
            toast.ShowMessage(toApraxxin ? "Clipboard converted to Apraxxin" : "Clipboard converted to English letters");
        }
        catch (ExternalException) { /* clipboard busy */ }
    }

    static bool IsStartupEnabled()
    {
        using var k = Registry.CurrentUser.OpenSubKey(RunKey);
        return k?.GetValue(RunName) is string;
    }

    void SetStartup(bool on)
    {
        using var k = Registry.CurrentUser.CreateSubKey(RunKey);
        if (on) k.SetValue(RunName, "\"" + Application.ExecutablePath + "\"");
        else k.DeleteValue(RunName, false);
        startupItem.Checked = IsStartupEnabled();
    }

    FontFamily? LoadEmbeddedFont()
    {
        try
        {
            using var s = typeof(TrayApp).Assembly.GetManifestResourceStream("Apraxxin.ttf");
            if (s == null) return null;
            var data = new byte[s.Length];
            for (int read = 0; read < data.Length;) read += s.Read(data, read, data.Length - read);
            IntPtr p = Marshal.AllocCoTaskMem(data.Length); // kept for the app's lifetime
            Marshal.Copy(data, 0, p, data.Length);
            fonts.AddMemoryFont(p, data.Length);
            return fonts.Families.FirstOrDefault();
        }
        catch { return null; }
    }

    Icon MakeIcon(bool on)
    {
        int size = SystemInformation.SmallIconSize.Width * 2;
        using var bmp = new Bitmap(size, size);
        using (var g = Graphics.FromImage(bmp))
        {
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.TextRenderingHint = TextRenderingHint.AntiAliasGridFit;
            using var bg = new SolidBrush(on ? Color.FromArgb(255, 196, 40) : Color.FromArgb(120, 120, 120));
            g.FillEllipse(bg, 0, 0, size - 1, size - 1);
            string glyph = apraxxinFamily != null ? "a" : "A";
            using var f = new Font(apraxxinFamily ?? FontFamily.GenericSansSerif, size * 0.55f, GraphicsUnit.Pixel);
            using var fg = new SolidBrush(on ? Color.Black : Color.White);
            var sz = g.MeasureString(glyph, f);
            g.DrawString(glyph, f, fg, (size - sz.Width) / 2, (size - sz.Height) / 2 + size * 0.04f);
        }
        return Icon.FromHandle(bmp.GetHicon());
    }

    protected override void ExitThreadCore()
    {
        hook.Dispose();
        tray.Visible = false;
        tray.Dispose();
        toast.Dispose();
        base.ExitThreadCore();
    }
}

/// <summary>Small non-activating on-screen notice shown when the mode changes.</summary>
sealed class Toast : Form
{
    readonly FontFamily? apraxxin;
    readonly System.Windows.Forms.Timer timer = new() { Interval = 1300 };
    string line1 = "", line2 = "";
    bool sample;

    public Toast(FontFamily? apraxxin)
    {
        this.apraxxin = apraxxin;
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        // No TopMost property here: WinForms' TopMost activates the window, which would
        // steal the keyboard from the app being typed in. WS_EX_TOPMOST is set below.
        StartPosition = FormStartPosition.Manual;
        BackColor = Color.FromArgb(32, 32, 32);
        Size = new Size(300, 86);
        DoubleBuffered = true;
        timer.Tick += (_, _) => { timer.Stop(); ShowWindow(Handle, SW_HIDE); shown = false; };
    }

    bool shown;
    const int SW_HIDE = 0, SW_SHOWNOACTIVATE = 4;
    const uint SWP_NOSIZE = 0x1, SWP_NOMOVE = 0x2, SWP_NOACTIVATE = 0x10, SWP_SHOWWINDOW = 0x40;
    [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);

    protected override bool ShowWithoutActivation => true;
    protected override CreateParams CreateParams
    {
        get
        {
            var cp = base.CreateParams;
            cp.ExStyle |= 0x08000000 /*NOACTIVATE*/ | 0x00000080 /*TOOLWINDOW*/ | 0x00000008 /*TOPMOST*/ | 0x00000020 /*TRANSPARENT*/;
            return cp;
        }
    }

    public void ShowState(bool on)
    {
        line1 = on ? "Apraxxin typing ON" : "Apraxxin typing OFF";
        line2 = on ? "apraxxin" : "";
        sample = on;
        Pop();
    }

    public void ShowMessage(string msg) { line1 = msg; line2 = ""; sample = false; Pop(); }

    void Pop()
    {
        var wa = Screen.FromPoint(Cursor.Position).WorkingArea;
        int x = wa.Right - Width - 16, y = wa.Bottom - Height - 16;
        // Show without ever activating, so typing keeps going to the user's program.
        SetWindowPos(Handle, new IntPtr(-1) /*HWND_TOPMOST*/, x, y, 0, 0, SWP_NOSIZE | SWP_NOACTIVATE);
        if (!shown) { ShowWindow(Handle, SW_SHOWNOACTIVATE); shown = true; }
        Invalidate();
        timer.Stop(); timer.Start();
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        g.TextRenderingHint = TextRenderingHint.AntiAliasGridFit;
        using var accent = new SolidBrush(sample ? Color.FromArgb(255, 196, 40) : Color.Gray);
        g.FillRectangle(accent, 0, 0, 6, Height);
        using var f1 = new Font("Segoe UI", 12f, FontStyle.Bold);
        g.DrawString(line1, f1, Brushes.White, 18, 12);
        if (sample && apraxxin != null)
        {
            using var f2 = new Font(apraxxin, 22f, GraphicsUnit.Pixel);
            g.DrawString(line2, f2, Brushes.White, 18, 44);
        }
    }

    protected override void Dispose(bool disposing) { if (disposing) timer.Dispose(); base.Dispose(disposing); }
}

/// <summary>Global low-level keyboard hook that rewrites keystrokes while enabled.</summary>
sealed class KeyboardHook : IDisposable
{
    public bool Enabled;
    public bool AcceptInjected;              // self-test only
    public static string? DebugLog = Environment.GetEnvironmentVariable("APRAXXIN_DEBUG_LOG");
    public event Action? Toggled;          // raised on the UI thread after the hotkey flipped Enabled
    public const long Marker = 0x41505258;   // "APRX" on our own SendInput events

    IntPtr hookId;
    readonly HookProc proc;                 // keep delegate alive
    Control? invoker;                       // runs Toggled on the UI thread, outside the hook
    readonly HashSet<int> swallowedDown = new();
    char prevChar = '\0';

    public KeyboardHook() { proc = Callback; }

    public void Install()
    {
        invoker = new Control();
        _ = invoker.Handle; // create the window now so BeginInvoke always works
        hookId = SetWindowsHookEx(WH_KEYBOARD_LL, proc, GetModuleHandle(null), 0);
        if (hookId == IntPtr.Zero) throw new Win32Exception();
    }

    public void Dispose()
    {
        if (hookId != IntPtr.Zero) UnhookWindowsHookEx(hookId);
        hookId = IntPtr.Zero;
        invoker?.Dispose();
    }

    IntPtr Callback(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode >= 0)
        {
            try
            {
                var k = Marshal.PtrToStructure<KBDLLHOOKSTRUCT>(lParam);
                bool injected = (k.flags & LLKHF_INJECTED) != 0;
                bool ours = k.dwExtraInfo == (IntPtr)Marker;
                bool swallow = (!injected || (AcceptInjected && !ours)) && Handle(k, (int)wParam);
                if (DebugLog != null)
                    File.AppendAllText(DebugLog, $"vk={k.vkCode:X2} msg={(int)wParam:X} inj={injected} ours={ours} en={Enabled} swallow={swallow} fg={GetForegroundWindow():X}\n");
                if (swallow)
                    return (IntPtr)1; // swallow
            }
            catch (Exception ex)
            {
                // Never let an error kill the app (that would silently stop Apraxxin typing).
                try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "ApraxxinKeyboard.log"), DateTime.Now + " " + ex + "\n"); } catch { }
            }
        }
        return CallNextHookEx(hookId, nCode, wParam, lParam);
    }

    bool Handle(KBDLLHOOKSTRUCT k, int msg)
    {
        bool down = msg == WM_KEYDOWN || msg == WM_SYSKEYDOWN;
        bool up = msg == WM_KEYUP || msg == WM_SYSKEYUP;
        int vk = (int)k.vkCode;

        // Toggle keys: Numpad Enter (Enter with the extended flag) or Ctrl+Shift+A.
        bool numpadEnter = vk == VK_RETURN && (k.flags & LLKHF_EXTENDED) != 0;
        bool ctrlShiftA = vk == VK_A && IsDown(VK_CONTROL) && IsDown(VK_SHIFT) && !IsDown(VK_MENU) && !IsDown(VK_LWIN) && !IsDown(VK_RWIN);
        if (numpadEnter || ctrlShiftA || (vk == VK_A && up && swallowedDown.Contains(-VK_A)))
        {
            if (vk == VK_A) vk = -VK_A; // remember the swallowed A separately from typed A
            if (down && !swallowedDown.Contains(vk))
            {
                swallowedDown.Add(vk);
                Enabled = !Enabled;          // flip immediately so the very next key is right
                if (invoker != null && Toggled != null) invoker.BeginInvoke(Toggled);
            }
            else if (up) swallowedDown.Remove(vk);
            return true;
        }

        if (up)
            return swallowedDown.Remove(vk);
        if (!down) return false;

        if (!Enabled) { Track(vk, null); return false; }

        // Leave shortcuts alone (Ctrl / Alt / Win, including AltGr).
        if (IsDown(VK_CONTROL) || IsDown(VK_MENU) || IsDown(VK_LWIN) || IsDown(VK_RWIN))
            return false;

        char? typed = CharFor(k);
        if (typed is char c && Apraxxin.Convert(c, prevChar) is char outChar)
        {
            SendChar(outChar);
            swallowedDown.Add(vk);
            prevChar = c;
            return true;
        }
        Track(vk, typed);
        return false;
    }

    // Remember enough context to choose opening/closing quotes.
    void Track(int vk, char? typed)
    {
        if (typed is char c) prevChar = c;
        else if (vk is VK_BACK) { /* unknown now; keep */ }
        else if (vk is VK_RETURN or VK_TAB or (>= 0x21 and <= 0x28)) prevChar = '\0'; // nav keys
    }

    static bool IsDown(int vk) => (GetAsyncKeyState(vk) & 0x8000) != 0;

    static char? CharFor(KBDLLHOOKSTRUCT k)
    {
        var state = new byte[256];
        if (IsDown(VK_SHIFT)) { state[VK_SHIFT] = 0x80; state[VK_LSHIFT] = 0x80; }
        if ((GetKeyState(VK_CAPITAL) & 1) != 0) state[VK_CAPITAL] = 0x01;
        if ((GetKeyState(VK_NUMLOCK) & 1) != 0) state[VK_NUMLOCK] = 0x01;
        IntPtr layout = GetKeyboardLayout(GetWindowThreadProcessId(GetForegroundWindow(), IntPtr.Zero));
        var buf = new System.Text.StringBuilder(8);
        // flag 4: do not change the keyboard state (keeps dead keys working)
        int n = ToUnicodeEx(k.vkCode, k.scanCode, state, buf, buf.Capacity, 4, layout);
        if (n == 1 && !char.IsControl(buf[0])) return buf[0];
        return null;
    }

    static void SendChar(char c)
    {
        var inputs = new INPUT[2];
        inputs[0].type = INPUT_KEYBOARD;
        inputs[0].ki = new KEYBDINPUT { wVk = 0, wScan = c, dwFlags = KEYEVENTF_UNICODE, dwExtraInfo = (IntPtr)Marker };
        inputs[1].type = INPUT_KEYBOARD;
        inputs[1].ki = new KEYBDINPUT { wVk = 0, wScan = c, dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, dwExtraInfo = (IntPtr)Marker };
        SendInput((uint)inputs.Length, inputs, Marshal.SizeOf<INPUT>());
    }

    // ---- Win32 ----
    const int WH_KEYBOARD_LL = 13, WM_KEYDOWN = 0x100, WM_KEYUP = 0x101, WM_SYSKEYDOWN = 0x104, WM_SYSKEYUP = 0x105;
    const uint LLKHF_EXTENDED = 0x01, LLKHF_INJECTED = 0x10;
    const int VK_A = 0x41, VK_BACK = 0x08, VK_TAB = 0x09, VK_RETURN = 0x0D, VK_SHIFT = 0x10, VK_CONTROL = 0x11, VK_MENU = 0x12,
              VK_CAPITAL = 0x14, VK_LWIN = 0x5B, VK_RWIN = 0x5C, VK_NUMLOCK = 0x90, VK_LSHIFT = 0xA0;
    const uint INPUT_KEYBOARD = 1, KEYEVENTF_KEYUP = 0x2, KEYEVENTF_UNICODE = 0x4;

    delegate IntPtr HookProc(int nCode, IntPtr wParam, IntPtr lParam);

    [StructLayout(LayoutKind.Sequential)]
    struct KBDLLHOOKSTRUCT { public uint vkCode, scanCode, flags, time; public IntPtr dwExtraInfo; }

    public static void SendCtrlShift(ushort vk)
    {
        var l = new List<INPUT>();
        void Add(ushort v, uint f) => l.Add(new INPUT { type = INPUT_KEYBOARD, ki = new KEYBDINPUT { wVk = v, dwFlags = f } });
        Add(VK_CONTROL, 0); Add(VK_SHIFT, 0); Add(vk, 0); Add(vk, KEYEVENTF_KEYUP); Add(VK_SHIFT, KEYEVENTF_KEYUP); Add(VK_CONTROL, KEYEVENTF_KEYUP);
        SendInput((uint)l.Count, l.ToArray(), Marshal.SizeOf<INPUT>());
    }

    public static void SendVk(ushort vk, bool shift = false, bool extended = false)
    {
        var list = new List<INPUT>();
        void Add(ushort v, uint flags) => list.Add(new INPUT { type = INPUT_KEYBOARD, ki = new KEYBDINPUT { wVk = v, dwFlags = flags } });
        uint ext = extended ? 1u : 0u;
        if (shift) Add(VK_SHIFT, 0);
        Add(vk, ext); Add(vk, ext | KEYEVENTF_KEYUP);
        if (shift) Add(VK_SHIFT, KEYEVENTF_KEYUP);
        SendInput((uint)list.Count, list.ToArray(), Marshal.SizeOf<INPUT>());
    }

    [StructLayout(LayoutKind.Sequential)]
    struct KEYBDINPUT { public ushort wVk, wScan; public uint dwFlags, time; public IntPtr dwExtraInfo; }

    [StructLayout(LayoutKind.Sequential)]
    struct MOUSEINPUT { public int dx, dy; public uint mouseData, dwFlags, time; public IntPtr dwExtraInfo; }

    [StructLayout(LayoutKind.Explicit)]
    struct INPUT
    {
        [FieldOffset(0)] public uint type;
        [FieldOffset(8)] public KEYBDINPUT ki;   // 8 = union offset on 64-bit
        [FieldOffset(8)] public MOUSEINPUT mi;   // sizes the union correctly
    }

    [DllImport("user32.dll", SetLastError = true)] static extern IntPtr SetWindowsHookEx(int id, HookProc fn, IntPtr mod, uint thread);
    [DllImport("user32.dll")] static extern bool UnhookWindowsHookEx(IntPtr h);
    [DllImport("user32.dll")] static extern IntPtr CallNextHookEx(IntPtr h, int n, IntPtr w, IntPtr l);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] static extern IntPtr GetModuleHandle(string? name);
    [DllImport("user32.dll")] static extern short GetAsyncKeyState(int vk);
    [DllImport("user32.dll")] static extern short GetKeyState(int vk);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hWnd, IntPtr pid);
    [DllImport("user32.dll")] static extern IntPtr GetKeyboardLayout(uint thread);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    static extern int ToUnicodeEx(uint vk, uint scan, byte[] state, System.Text.StringBuilder buf, int cch, uint flags, IntPtr hkl);
    [DllImport("user32.dll", SetLastError = true)] static extern uint SendInput(uint n, INPUT[] inputs, int size);
}

/// <summary>Automated check: types into its own text box through the real hook.</summary>
static class SelfTest
{
    public static int Run(string reportPath)
    {
        var form = new Form { Text = "Apraxxin self-test", Width = 700, Height = 160, TopMost = true, StartPosition = FormStartPosition.CenterScreen };
        var box = new TextBox { Dock = DockStyle.Fill, Multiline = true, Font = new Font("Segoe UI", 16f) };
        form.Controls.Add(box);
        var app = new TrayApp(false, acceptInjected: true);
        string result = "";
        int code = 1;
        form.Shown += async (_, _) =>
        {
            // Only type if our own window really has the keyboard focus, so test keys can
            // never land in another program.
            for (int i = 0; i < 10 && GetForegroundWindow() != form.Handle; i++)
            {
                form.TopMost = true; form.Activate(); SetForegroundWindow(form.Handle);
                await Task.Delay(200);
            }
            box.Focus();
            await Task.Delay(300);
            if (GetForegroundWindow() != form.Handle || !box.Focused)
            {
                File.WriteAllText(reportPath, "SKIPPED: could not get keyboard focus for the test window\n");
                code = 3; app.Shutdown(); form.Close(); return;
            }
            // "ab" (off)  NumpadEnter  He said "it's ok" - Shift+-  NumpadEnter  "z"
            void T(ushort vk, bool sh = false, bool ext = false) => KeyboardHook.SendVk(vk, sh, ext);
            T(0x41); T(0x42);
            T(0x0D, ext: true);
            T(0x48, sh: true); T(0x45); T(0x20); T(0x53); T(0x41); T(0x49); T(0x44); T(0x20);
            T(0xDE, sh: true); T(0x49); T(0x54); T(0xDE); T(0x53); T(0x20); T(0x4F); T(0x4B); T(0xDE, sh: true);
            T(0x20); T(0xBD); T(0x20); T(0xBD, sh: true); T(0x31); T(0x30); T(0x31, sh: true); T(0x32, sh: true);
            KeyboardHook.SendCtrlShift(0x41);  // Ctrl+Shift+A turns it off
            T(0x5A);
            KeyboardHook.SendCtrlShift(0x41);  // ...and on again
            T(0x5A);
            T(0x0D, ext: true);               // Numpad Enter turns it off
            T(0x5A);
            await Task.Delay(800);
            result = box.Text;
            string expected = "ab" + Apraxxin.ToApraxxin("He said \"it's ok\" - _10!") + "@z" + Apraxxin.ToApraxxin("z") + "z";
            code = result == expected ? 0 : 2;
            File.WriteAllText(reportPath,
                (code == 0 ? "PASS" : "FAIL") + "\nexpected: " + Hex(expected) + "\nactual:   " + Hex(result) +
                $"\nform={form.Handle:X} box={box.Handle:X} fg={GetForegroundWindow():X} focused={box.Focused}\n");
            app.Shutdown();
            form.Close();
        };
        Application.Run(form);
        return code;
    }

    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);

    static string Hex(string s) => string.Join(" ", s.Select(c => c < 128 ? c.ToString() : ((int)c).ToString("X4")));
}
