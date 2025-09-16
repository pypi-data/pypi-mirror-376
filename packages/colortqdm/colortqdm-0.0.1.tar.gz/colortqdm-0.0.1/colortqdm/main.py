import re, shutil
from collections import defaultdict
from tqdm import tqdm
import numpy as np

# --- small utilities ---------------------------------------------------------

def _fg_true(r,g,b): return f"\033[38;2;{r};{g};{b}m"
def _bg_true(r,g,b): return f"\033[48;2;{r};{g};{b}m"

def _fmt(secs):
    try:
        s = int(round(float(secs)))
        if s < 0: return ""
    except Exception:
        return ""
    m, s = divmod(s, 60); h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"

_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
def _vislen(s): return len(_ANSI_RE.sub("", s or ""))

def _commas(x):
    try: return f"{int(x):,d}"
    except Exception: return str(x)

def _pct3(part, total):
    try:
        if not total or total <= 0: return ""
        return f"{(100.0*float(part)/float(total)):.3g}%"
    except Exception:
        return ""

def _as_color_key(x):
    if x is None:
        return None
    if isinstance(x, str):
        return x.lower()
    # allow tuple/list/np array of 3 ints/floats
    try:
        if len(x) == 3:
            r, g, b = (int(float(x[0])), int(float(x[1])), int(float(x[2])))
            r = 0 if r < 0 else (255 if r > 255 else r)
            g = 0 if g < 0 else (255 if g > 255 else g)
            b = 0 if b < 0 else (255 if b > 255 else b)
            return (r, g, b)
    except Exception:
        pass
    # fallback – keep behavior predictable
    return str(x).lower()

# --- progress bar ------------------------------------------------------------

class colortqdm(tqdm):
    """
    tqdm with per-step colors and short labels:
      pbar.update(1, color="yellow"), pbar.update(1, name="Y")
      pbar.update(1, color=(128,16,222))  # arbitrary RGB truecolor
    """

    _PALETTE = {
        "blue": (31,119,180), "orange": (255,127,14), "green": (44,160,44),
        "red": (214,39,40), "purple": (148,103,189), "brown": (140,86,75),
        "magenta": (227,119,194), "grey": (127,127,127), "gray": (127,127,127),
        "yellow": (188,189,34), "white": (255,255,255)
    }
    _ANSI = {c:_fg_true(*rgb) for c,rgb in _PALETTE.items()}
    _ANSI.update({"black":"\033[30m","dim":"\033[90m","fgreset":"\033[39m","bgreset":"\033[49m","reset":"\033[0m",None:""})
    _ANSI_BG = {c:_bg_true(*rgb) for c,rgb in _PALETTE.items()}
    _ANSI_BG[None] = ""
    _order = ["green","blue","orange","red","purple","brown","magenta","grey","gray","yellow","white"]

    def __init__(self, *args, default_color="white", bar_char="█", empty_char=" ", **kwargs):
        self._cbar = ""
        self._counts = defaultdict(int)   # color -> steps
        self._labels = {}                 # color -> short name
        kwargs["bar_format"] = "{cbar}"
        super().__init__(*args, **kwargs)
        try:
            import colorama; colorama.just_fix_windows_console()  # type: ignore
        except Exception:
            pass
        self.default_color = _as_color_key(default_color or "white")
        self.bar_char = bar_char           # kept for API compatibility
        self.empty_char = empty_char
        self._render()

    @property
    def format_dict(self):
        d = super().format_dict
        d["cbar"] = self._cbar
        return d

    def update(self, n=1, color=None, name=None):
        c = self.default_color if color is None else _as_color_key(color)
        if n > 0:
            self._counts[c] += n
            if name is not None: self._labels[c] = str(name)
        r = super().update(n)
        self._render()
        return r

    # --- internals -----------------------------------------------------------

    def _ansi(self, name):
        if isinstance(name, (tuple, list)) and len(name) == 3:
            r, g, b = (int(name[0]), int(name[1]), int(name[2]))
            return _fg_true(r, g, b)
        return self._ANSI.get(name, "")

    def _bg(self, name):
        if isinstance(name, (tuple, list)) and len(name) == 3:
            r, g, b = (int(name[0]), int(name[1]), int(name[2]))
            return _bg_true(r, g, b)
        return self._ANSI_BG.get(name, "")

    def _term_cols(self):
        return (self.ncols if isinstance(self.ncols, int) and self.ncols > 0
                else shutil.get_terminal_size(fallback=(80,24)).columns)

    def _truncate(self, s, k):
        if k <= 0: return ""
        return s if len(s) <= k else ("…" if k == 1 else "…" + s[-(k-1):])

    def _present_ordered(self):
        present = [c for c,v in self._counts.items() if v > 0]
        return [c for c in self._order if c in present] + [c for c in present if c not in self._order]

    def _alloc_cells(self, filled):
        if self.n <= 0 or filled <= 0: return []
        cols = self._present_ordered()
        if not cols: return []
        counts = np.array([self._counts.get(c,0) for c in cols], dtype=float)
        total = counts.sum()
        if total <= 0: return []
        exact = counts/total * filled
        floors = np.floor(exact).astype(int)
        leftover = max(0, filled - int(floors.sum()))
        if leftover:
            order = np.lexsort((-np.arange(len(cols)), exact - floors))  # by remainder desc, then original order
            for i in order[:leftover]: floors[i] += 1
        return [(c, k) for c,k in zip(cols, floors) if k > 0]

    def _counts_text(self):
        present = self._present_ordered()
        if len(present) == 1:
            left = _commas(self.n)
        else:
            parts = [f"{self._ansi(c)}{_commas(self._counts.get(c,0))}{self._ansi('reset')}" for c in present]
            left = ":".join(parts) if parts else _commas(self.n)
        # when total is unknown, show the running count instead of "?"
        all_str = _commas(self.total) if isinstance(self.total,int) and self.total > 0 else _commas(self.n)
        return f"{left}/{all_str}"

    def _overlay(self, width, label, pct):
        label, pct = (label or "").strip(), (pct or "").strip()
        for t in (f"{label} {pct}".strip(), pct, label):
            if t and width >= len(t): return t
        return ""

    def _render(self):
        cols = self._term_cols()
        tot = self.total if (self.total and self.total > 0) else None
        n = min(self.n, tot) if tot else self.n
        # No overall percent when total is unknown; still fill bar to 100%.
        perc_str = f"{(n/tot*100):3.0f}%" if tot else ""

        f = super().format_dict
        elapsed = _fmt(f.get("elapsed", 0.0))
        remaining_val = f.get("remaining", None)
        rate = f.get("rate", None)
        if remaining_val is None and tot and isinstance(rate,(int,float)) and rate > 0:
            remaining_val = max(0.0, (tot - self.n) / rate)
        remaining = _fmt(remaining_val) if isinstance(remaining_val,(int,float)) else ""
        unit = (self.unit or "it").strip() if getattr(self,"unit",None) else "it"
        rate_str = f"{rate:,.2f} {unit}/s" if isinstance(rate,(int,float)) and rate > 0 else ""

        bracket_items = [p for p in (f"{elapsed}<{remaining}" if remaining else elapsed, rate_str) if p]
        suffix = f"| {self._counts_text()}" + (f" [{',  '.join(bracket_items)}]" if bracket_items else "")

        MIN_BAR = 10
        fixed_left = len(perc_str) + 1
        fixed_right = _vislen(suffix)
        avail = cols - fixed_left - fixed_right
        desc_max = 0 if avail < MIN_BAR else (avail - MIN_BAR)
        desc = self._truncate((self.desc or "").strip(), desc_max) if desc_max > 0 else ""
        prefix = f"{self._ansi('reset')}{(desc + ': ') if desc else ''}{perc_str}|"

        bar_width = max(1, cols - _vislen(prefix) - fixed_right)
        # Fill the bar fully when total is unknown
        filled = min(bar_width, int(round(n * bar_width / tot))) if tot else bar_width

        # If only one color is present, do not overlay percent on the sub-bar
        single_color_present = (len(self._present_ordered()) == 1)

        parts = []
        for c,k in self._alloc_cells(filled):
            # Keep percent labels on sub-bars unless only one color is present.
            if tot:
                pct_text = "" if single_color_present else _pct3(self._counts.get(c,0), tot)
            else:
                seen_total = sum(self._counts.values())
                pct_text = "" if single_color_present else _pct3(self._counts.get(c,0), seen_total)
            text = self._overlay(k, self._labels.get(c,""), pct_text)
            if text:
                left = (k - len(text)) // 2
                parts.append(f"{self._bg(c)}{' ' * left}{self._ansi('black')}{text}{self._ansi('fgreset')}{' ' * (k - left - len(text))}")
            else:
                parts.append(f"{self._bg(c)}{' ' * k}")

        empty = max(0, bar_width - filled)
        if empty: parts.append(f"{self._ansi('bgreset')}{self._ansi('dim')}{self.empty_char * empty}")
        parts.append(self._ansi("reset"))

        self._cbar = f"{prefix}{''.join(parts)}{suffix}{self._ansi('reset')}"

    # ensure final frame is rendered (especially important right at completion)
    def close(self):
        # If we somehow end a few short of total (due to caller behavior or display throttling),
        # make sure tqdm finishes cleanly visually.
        if isinstance(self.total, int) and self.total > 0 and self.n < self.total:
            super().update(self.total - self.n)
        self._render()
        self.refresh()
        super().close()
