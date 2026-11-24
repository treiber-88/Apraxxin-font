// Apraxxin for Chrome: lets pages show Apraxxin characters (Unicode Private Use
// Area U+E000-U+E0FF) using the locally installed Apraxxin font.
//
// Chrome does not use Windows' EUDC font link, so for every font family a page
// uses we add an extra face that covers only the Apraxxin code points. Normal
// letters keep rendering exactly as before.
(() => {
  const RANGE = "U+E000-E0FF";
  const SRC = 'local("Apraxxin"), local("Apraxxin Regular"), local("Apraxxin-Regular")';
  // Windows fonts that pages often name without loading them as web fonts.
  const SYSTEM = new Set(["arial", "segoe ui", "segoe ui historic", "segoe ui variable", "calibri", "cambria",
    "candara", "consolas", "constantia", "corbel", "courier new", "georgia", "tahoma", "times new roman",
    "trebuchet ms", "verdana", "comic sans ms", "impact", "lucida console", "lucida sans unicode",
    "palatino linotype", "franklin gothic medium", "sitka text", "cascadia code", "cascadia mono"]);
  // Families we always cover (canvas-drawn apps like Google Docs name these).
  const ALWAYS = ["Arial", "Segoe UI", "Calibri", "Times New Roman", "Courier New", "Verdana", "Georgia",
    "Roboto", "Open Sans", "Google Sans", "Google Sans Text", "Lato", "Montserrat", "Inter", "Noto Sans",
    "Helvetica Neue", "Helvetica", "gg sans", "Whitney"];
  const GENERIC = new Set(["serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "math",
    "emoji", "fangsong", "ui-serif", "ui-sans-serif", "ui-monospace", "ui-rounded", "-apple-system",
    "blinkmacsystemfont", "inherit", "initial", "unset", "revert"]);
  const ours = new WeakSet();
  const twins = new Set();
  const localDone = new Set();

  const strip = (n) => n.trim().replace(/^["']|["']$/g, "");
  const pageFaces = (key) => [...document.fonts].filter((f) => !ours.has(f) && strip(f.family).toLowerCase() === key);

  function add(family, source, desc) {
    try {
      const face = new FontFace(family, source, desc);
      ours.add(face);
      document.fonts.add(face);
      face.load().catch(() => {});
    } catch (e) { /* invalid name */ }
  }

  // Chrome builds a family from faces with identical weight/style/stretch, so the
  // Apraxxin face must copy the descriptors of every real face exactly.
  function twin(family, desc) {
    const k = family.toLowerCase() + "|" + desc.weight + "|" + desc.style + "|" + (desc.stretch || "normal");
    if (twins.has(k)) return;
    twins.add(k);
    add(family, SRC, { ...desc, unicodeRange: RANGE });
  }

  function cover(name) {
    const key = name.toLowerCase();
    if (!key || GENERIC.has(key)) return;
    const faces = pageFaces(key);
    if (faces.length) {
      // web font defined by the page: join each of its faces
      for (const f of faces) twin(name, { weight: f.weight, style: f.style, stretch: f.stretch });
      return;
    }
    if (localDone.has(key)) return;
    localDone.add(key);
    // A locally installed font named directly. Defining the family name hides the
    // installed font, so re-add it (if it is not installed these faces simply fail
    // and the browser moves on to the next family, exactly as before).
    const q = (s) => `local("${s}")`;
    const sets = [
      [{ weight: "1 549", style: "normal" }, q(name)],
      [{ weight: "550 1000", style: "normal" }, `${q(name + " Bold")}, ${q(name)}`],
      [{ weight: "1 549", style: "italic" }, `${q(name + " Italic")}, ${q(name)}`],
      [{ weight: "550 1000", style: "italic" }, `${q(name + " Bold Italic")}, ${q(name + " Bold")}, ${q(name)}`],
    ];
    for (const [desc, src] of sets) { add(name, src, desc); twin(name, desc); }
  }

  function scanFamilies(root) {
    const els = root.querySelectorAll ? [root, ...root.querySelectorAll("*")] : [];
    const seen = new Set();
    for (const el of els) {
      const ff = getComputedStyle(el).fontFamily;
      if (seen.has(ff)) continue;
      seen.add(ff);
      for (const part of ff.split(",")) cover(strip(part));
    }
  }

  let pending = false;
  const rescan = () => {
    if (pending) return;
    pending = true;
    setTimeout(() => { pending = false; if (document.documentElement) scanFamilies(document.documentElement); }, 400);
  };
  new MutationObserver(rescan).observe(document, { childList: true, subtree: true });
  document.fonts.addEventListener?.("loadingdone", rescan);
  // Wait for the page's own @font-face rules before deciding what is a web font.
  document.fonts.ready.then(() => { ALWAYS.forEach(cover); rescan(); });
  rescan();
})();
