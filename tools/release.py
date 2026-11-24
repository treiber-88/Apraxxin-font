"""Rebuild everything and assemble the ready-to-use folder  <project>/Apraxxin/

  python tools/release.py
"""
import base64, html, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "Apraxxin")


def run(cmd, **kw):
    print(">", " ".join(cmd))
    subprocess.run(cmd, check=True, **kw)


def chart_html(font_path):
    b64 = base64.b64encode(open(font_path, "rb").read()).decode()
    P = lambda s: "".join(chr(0xE000 + ord(c)) for c in s)
    rows = []
    groups = [
        ("Letters", [(c, P(c), P(c.upper())) for c in "abcdefghijklmnopqrstuvwxyz"]),
        ("Numbers", [(c, P(c), "") for c in "1234567890"]),
        ("Punctuation", [(c, P(c), "") for c in ":;,./\\+-=!?&*()[]{}"] + [
            ('" (opening)', P('"'), ""), ('" (closing)', "", ""),
            ("' (apostrophe / closing)", P("'"), ""), ("' (opening)", P("`"), ""),
            ("Shift + -  (em dash)", "", "")]),
    ]
    for title, items in groups:
        cells = "".join(
            f'<div class="c"><div class="k">{html.escape(k)}</div><div class="g">{g}</div>'
            + (f'<div class="g cap">{u}</div>' if u else "") + "</div>" for k, g, u in items)
        rows.append(f"<h2>{title}</h2><div class=\"grid\">{cells}</div>")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Apraxxin chart</title>
<style>
@font-face {{ font-family: "ApraxxinChart"; src: url(data:font/ttf;base64,{b64}) format("truetype"); }}
:root {{ --bg:#faf8f4; --fg:#1d1b18; --muted:#6d675e; --card:#fff; --line:#e4ded3; --accent:#b7791f; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#1b1a18; --fg:#f1ede6; --muted:#a49d92; --card:#252320; --line:#38342f; --accent:#e0a23a; }} }}
body {{ margin:0; padding:24px 16px 48px; background:var(--bg); color:var(--fg); font:16px/1.5 "Segoe UI",system-ui,sans-serif; }}
main {{ max-width:960px; margin:0 auto; }}
h1 {{ margin:0 0 4px; font-size:28px; }} h2 {{ margin:28px 0 10px; font-size:18px; color:var(--accent); }}
p {{ color:var(--muted); margin:4px 0; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(104px,1fr)); gap:8px; }}
.c {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:8px 6px; text-align:center; }}
.k {{ font-size:13px; color:var(--muted); min-height:20px; }}
.g {{ font-family:"ApraxxinChart"; font-size:40px; line-height:1.35; }}
.cap {{ font-size:28px; border-top:1px dashed var(--line); }}
textarea {{ width:100%; box-sizing:border-box; min-height:70px; font:20px "Segoe UI",sans-serif; padding:8px; border-radius:8px; border:1px solid var(--line); background:var(--card); color:var(--fg); }}
#out {{ font-family:"ApraxxinChart","Segoe UI",sans-serif; font-size:34px; min-height:50px; margin-top:8px; overflow-wrap:anywhere; }}
kbd {{ border:1px solid var(--line); border-bottom-width:2px; border-radius:4px; padding:0 5px; background:var(--card); }}
</style></head><body><main>
<h1>Apraxxin</h1>
<p>Press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> or <kbd>Numpad Enter</kbd> to switch Apraxxin typing on or off. Capitals (with <kbd>Shift</kbd> or Caps Lock) get the line above.</p>
<h2>Try it</h2>
<textarea id="in" placeholder="Type ordinary letters here…">Hello, world!</textarea>
<div id="out"></div>
{''.join(rows)}
</main><script>
const inp=document.getElementById('in'), out=document.getElementById('out');
const direct=/[a-zA-Z0-9:;,\\/\\\\+\\-=!.?&*()\\[\\]{{}}]/;
function conv(s){{let r='',prev='';for(const c of s){{const open=!prev||/\\s|[(\\[{{]/.test(prev);
if(direct.test(c))r+=String.fromCharCode(0xE000+c.charCodeAt(0));
else if(c=='"')r+=open?'\\uE022':'\\uE080';else if(c=="'")r+=open?'\\uE060':'\\uE027';
else if(c=='_')r+='\\uE081';else if(c==' ')r+='\\u2002';else r+=c;prev=c;}}return r;}}
const upd=()=>out.textContent=conv(inp.value);inp.addEventListener('input',upd);upd();
</script></body></html>"""


def main():
    run([sys.executable, os.path.join(HERE, "build_font.py")])
    font = os.path.join(ROOT, "build", "Apraxxin.ttf")
    # .NET Framework 4.8 build: one small exe that runs on any Windows 10/11 PC.
    run(["dotnet", "build", os.path.join(ROOT, "keyboard", "ApraxxinKeyboard.csproj"), "-c", "Release"])
    exe = os.path.join(ROOT, "keyboard", "bin", "Release", "net48", "ApraxxinKeyboard.exe")

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)  # generated folder: rebuild it from scratch so nothing stale is shipped
    os.makedirs(OUT)
    shutil.copy2(font, OUT)
    shutil.copy2(exe, OUT)
    shutil.copy2(os.path.join(ROOT, "installer", "README.md"), OUT)
    ext = os.path.join(OUT, "chrome-extension")
    os.makedirs(ext, exist_ok=True)
    for f in ("manifest.json", "content.js"):
        shutil.copy2(os.path.join(ROOT, "chrome-extension", f), ext)
    for f in ("install.ps1", "uninstall.ps1"):
        shutil.copy2(os.path.join(ROOT, "installer", f), OUT)
    cmd = '@echo off\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0{0}" {1}\r\npause\r\n'
    with open(os.path.join(OUT, "Install Apraxxin.cmd"), "w", newline="") as f:
        f.write(cmd.format("install.ps1", ""))
    with open(os.path.join(OUT, "Install font only (to read Apraxxin).cmd"), "w", newline="") as f:
        f.write(cmd.format("install.ps1", "-FontOnly"))
    with open(os.path.join(OUT, "Uninstall Apraxxin.cmd"), "w", newline="") as f:
        f.write(cmd.format("uninstall.ps1", ""))
    with open(os.path.join(OUT, "Apraxxin chart.html"), "w", encoding="utf-8") as f:
        f.write(chart_html(font))
    zip_base = os.path.join(ROOT, "Apraxxin")
    shutil.make_archive(zip_base, "zip", ROOT, "Apraxxin")
    print("release folder:", OUT)
    print("zip to send:   ", zip_base + ".zip")


if __name__ == "__main__":
    main()
