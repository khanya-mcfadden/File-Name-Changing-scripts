import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import tkinter.ttk as ttk

# ── Core logic ────────────────────────────────────────────────────────────────

def smart_capitalize(text):
    return re.sub(
        r'\b([a-zA-Z])([a-zA-Z]*)',
        lambda m: m.group(1).upper() + m.group(2).lower(),
        text
    )

def run_capitalize(directory, log):
    renamed = skipped = 0
    for filename in os.listdir(directory):
        full_path = os.path.join(directory, filename)
        if not os.path.isfile(full_path):
            continue
        name, ext = os.path.splitext(filename)
        new_filename = smart_capitalize(name) + ext
        if new_filename == filename:
            continue
        new_path = os.path.join(directory, new_filename)
        if os.path.exists(new_path) and new_path.lower() != full_path.lower():
            log(f"Skipped (already exists): {new_filename}")
            skipped += 1
        else:
            temp = full_path + ".__temp__"
            os.rename(full_path, temp)
            os.rename(temp, new_path)
            log(f"Renamed: {filename}  →  {new_filename}")
            renamed += 1
    log(f"\nDone. Renamed: {renamed} | Skipped: {skipped}")

def run_add_prefix(directory, prefix, log):
    renamed = skipped = 0
    script_name = os.path.basename(__file__)
    for filename in os.listdir(directory):
        full_path = os.path.join(directory, filename)
        if not os.path.isfile(full_path):
            continue
        if filename == script_name:
            continue
        if filename.startswith(prefix):
            log(f"Skipped (already has prefix): {filename}")
            skipped += 1
            continue
        new_filename = prefix + filename
        new_path = os.path.join(directory, new_filename)
        if not os.path.exists(new_path):
            os.rename(full_path, new_path)
            log(f"Renamed: {filename}  →  {new_filename}")
            renamed += 1
        else:
            log(f"Skipped (name exists): {new_filename}")
            skipped += 1
    log(f"\nDone. Renamed: {renamed} | Skipped: {skipped}")

# ── NEW: Dynamic prefix removal logic ─────────────────────────────────────────
#
# Pattern syntax understood by parse_removal_pattern():
#
#   <fixed_prefix>(N)<trailing>
#
#   fixed_prefix  – any literal text before the dynamic segment (may be empty)
#   (N)           – integer N inside parentheses → remove exactly N characters
#                   at the position where the dynamic segment starts
#   trailing      – any literal text immediately after (N) that should also
#                   be stripped (may be empty)
#
# Examples:
#   "Koikatu_F_(19)"   → fixed="Koikatu_F_",  n=19, trailing=""
#   "F_(9)_"           → fixed="F_",           n=9,  trailing="_"
#   "(12)"             → fixed="",             n=12, trailing=""
#   "RAW_"             → no (N) marker → treated as a plain fixed prefix
#                        (falls through to the original removal path)

def parse_removal_pattern(pattern):
    """
    Parse a removal pattern that may contain a (N) dynamic-length marker.

    Returns a dict with:
        'fixed'    – literal prefix before the (N) marker (str)
        'n'        – number of dynamic characters to remove (int or None)
        'trailing' – literal suffix after the (N) marker (str)
        'dynamic'  – True when a (N) marker was found, False otherwise

    When 'dynamic' is False the caller should fall back to plain prefix removal.
    """
    # Match optional leading text, then (digits), then optional trailing text.
    # The entire pattern must be consumed – we do not allow anything after
    # the trailing part so the caller can safely anchor to filename start.
    m = re.fullmatch(r'(.*?)\((\d+)\)(.*)', pattern)
    if m:
        return {
            'dynamic':  True,
            'fixed':    m.group(1),   # literal text before (N)
            'n':        int(m.group(2)),  # characters to skip dynamically
            'trailing': m.group(3),   # literal text after (N)
        }
    # No (N) marker → plain fixed-prefix pattern
    return {
        'dynamic':  False,
        'fixed':    pattern,
        'n':        None,
        'trailing': '',
    }


def apply_removal_pattern(filename, parsed):
    """
    Apply a parsed removal pattern to a single filename.

    Returns the new filename string if the pattern matched, or None if it
    did not apply (so the caller can skip / log accordingly).

    Logic:
        1. The filename must start with `fixed`.
        2. After `fixed`, skip exactly `n` characters (the dynamic segment).
        3. The characters immediately following must equal `trailing`.
        4. Everything from (fixed + n + trailing) onward is kept.
    """
    fixed    = parsed['fixed']
    n        = parsed['n']
    trailing = parsed['trailing']

    if not parsed['dynamic']:
        # Plain fixed-prefix removal – same behaviour as the original function
        if filename.startswith(fixed):
            return filename[len(fixed):]
        return None   # pattern doesn't match this filename

    # --- dynamic path ---

    # Step 1: filename must start with the fixed prefix
    if not filename.startswith(fixed):
        return None

    # Step 2: measure the removal window
    removal_start = len(fixed)          # index right after the fixed prefix
    removal_end   = removal_start + n   # end of the dynamic segment

    # Guard: ensure there are at least n characters available after the prefix
    if len(filename) < removal_end:
        return None   # not enough characters – skip safely

    # Step 3: after the dynamic segment, the trailing string must be present
    after_dynamic = filename[removal_end:]
    if not after_dynamic.startswith(trailing):
        return None   # trailing text not found – pattern doesn't match

    # Step 4: build the new filename by cutting out fixed + n_chars + trailing
    kept = after_dynamic[len(trailing):]   # everything after the trailing text
    new_name = kept if kept else None      # don't produce an empty filename

    return new_name
# ── END new dynamic removal logic ─────────────────────────────────────────────


def run_remove_prefix(directory, prefix, log):
    """
    Remove a prefix (plain or dynamic) from every file in `directory`.

    The `prefix` argument is first passed through parse_removal_pattern().
    If it contains a (N) marker the dynamic path is used; otherwise the
    original fixed-string removal runs unchanged.
    """
    renamed = skipped = 0

    # Parse the pattern once; reuse for every file in the directory
    # NEW: parse_removal_pattern() handles both plain and dynamic patterns
    parsed = parse_removal_pattern(prefix)

    # Log which mode is active so the user can verify the intent
    if parsed['dynamic']:
        log(
            f"── Pattern parsed  →  fixed='{parsed['fixed']}'  "
            f"dynamic_chars={parsed['n']}  trailing='{parsed['trailing']}'"
        )

    for filename in os.listdir(directory):
        full_path = os.path.join(directory, filename)
        if not os.path.isfile(full_path):
            continue

        # NEW: use apply_removal_pattern() for both dynamic and plain modes
        new_name = apply_removal_pattern(filename, parsed)

        if new_name is None:
            # Pattern did not match this file – leave it untouched
            continue

        if new_name == filename:
            # Nothing would change
            continue

        new_path = os.path.join(directory, new_name)
        if not os.path.exists(new_path):
            os.rename(full_path, new_path)
            log(f"Renamed: {filename}  →  {new_name}")
            renamed += 1
        else:
            log(f"Skipped (already exists): {new_name}")
            skipped += 1

    log(f"\nDone. Renamed: {renamed} | Skipped: {skipped}")

# ── GUI ───────────────────────────────────────────────────────────────────────

BG       = "#1a1a2e"
PANEL    = "#16213e"
ACCENT   = "#e94560"
ACCENT2  = "#0f3460"
TEXT     = "#eaeaea"
MUTED    = "#8892a4"
MONO     = ("Consolas", 10)
TITLE_F  = ("Georgia", 22, "bold")
LABEL_F  = ("Segoe UI", 10)
BTN_F    = ("Segoe UI", 10, "bold")

class FileRenamerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Renamer Suite")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(680, 580)

        self._build_ui()
        self.update_idletasks()
        w, h = 740, 640
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── layout ----------------------------------------------------------------

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=ACCENT2, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="File Renamer Suite", font=TITLE_F,
                 bg=ACCENT2, fg=TEXT).pack()
        tk.Label(hdr, text="Capitalize · Add Prefix · Remove Prefix",
                 font=("Segoe UI", 10), bg=ACCENT2, fg=MUTED).pack()

        # Body
        body = tk.Frame(self, bg=BG, padx=24, pady=16)
        body.pack(fill="both", expand=True)

        # Directory row
        dir_frame = tk.Frame(body, bg=BG)
        dir_frame.pack(fill="x", pady=(0, 14))
        tk.Label(dir_frame, text="Directory", font=LABEL_F,
                 bg=BG, fg=MUTED, width=12, anchor="w").pack(side="left")
        self.dir_var = tk.StringVar()
        tk.Entry(dir_frame, textvariable=self.dir_var,
                 font=MONO, bg=PANEL, fg=TEXT,
                 insertbackground=TEXT, relief="flat",
                 highlightthickness=1, highlightcolor=ACCENT,
                 highlightbackground=ACCENT2).pack(side="left", fill="x", expand=True, padx=(0,8))
        self._btn(dir_frame, "Browse…", self._browse).pack(side="left")

        # Operation tabs
        nb = ttk.Notebook(body)
        nb.pack(fill="x", pady=(0, 14))
        self._style_notebook()

        self.tab_cap  = tk.Frame(nb, bg=PANEL, padx=12, pady=12)
        self.tab_add  = tk.Frame(nb, bg=PANEL, padx=12, pady=12)
        self.tab_rem  = tk.Frame(nb, bg=PANEL, padx=12, pady=12)
        nb.add(self.tab_cap, text="  Capitalize  ")
        nb.add(self.tab_add, text="  Add Prefix  ")
        nb.add(self.tab_rem, text="  Remove Prefix  ")

        # Capitalize tab
        tk.Label(self.tab_cap,
                 text="Capitalizes the first letter of each word in every filename.",
                 font=LABEL_F, bg=PANEL, fg=MUTED, wraplength=580, justify="left"
                 ).pack(anchor="w")

        # Add prefix tab
        self._prefix_add_var = tk.StringVar()
        self._make_prefix_row(
            self.tab_add,
            "Prefix to add:",
            self.tab_add,
            self._prefix_add_var,
            tip="Leave blank to use the folder name as prefix (adds underscore automatically)."
        )

        # Remove prefix tab – updated tip explains the new (N) syntax
        self._prefix_rem_var = tk.StringVar()
        self._make_prefix_row(
            self.tab_rem,
            "Prefix to remove:",
            self.tab_rem,
            self._prefix_rem_var,
            # NEW: tip updated to document the dynamic (N) marker syntax
            tip=(
                "Enter the exact prefix to strip from filenames.  "
                "Dynamic removal: use (N) to skip N characters at that position.  "
                "Examples:  'Koikatu_F_(19)'  strips 'Koikatu_F_' then the next 19 chars;  "
                "'F_(9)_'  strips 'F_', the next 9 chars, and the trailing '_'."
            )
        )

        # Run button
        run_frame = tk.Frame(body, bg=BG)
        run_frame.pack(fill="x", pady=(0, 12))
        self._btn(run_frame, "▶  Run", self._run, big=True).pack(side="right")
        self._btn(run_frame, "Clear Log", self._clear_log, secondary=True).pack(side="right", padx=(0,8))

        # Log
        tk.Label(body, text="Output Log", font=LABEL_F,
                 bg=BG, fg=MUTED).pack(anchor="w")
        self.log_box = scrolledtext.ScrolledText(
            body, font=MONO, bg=PANEL, fg=TEXT,
            insertbackground=TEXT, relief="flat",
            highlightthickness=1, highlightcolor=ACCENT2,
            highlightbackground=ACCENT2,
            state="disabled", height=12
        )
        self.log_box.pack(fill="both", expand=True, pady=(4,0))

        self._nb = nb

    def _make_prefix_row(self, parent, label, frame, var, tip=""):
        row = tk.Frame(frame, bg=PANEL)
        row.pack(fill="x", pady=(0,6))
        tk.Label(row, text=label, font=LABEL_F,
                 bg=PANEL, fg=MUTED, width=16, anchor="w").pack(side="left")
        tk.Entry(row, textvariable=var,
                 font=MONO, bg=BG, fg=TEXT,
                 insertbackground=TEXT, relief="flat",
                 highlightthickness=1, highlightcolor=ACCENT,
                 highlightbackground=ACCENT2).pack(side="left", fill="x", expand=True)
        if tip:
            tk.Label(frame, text=tip, font=("Segoe UI", 9),
                     bg=PANEL, fg=MUTED, wraplength=560, justify="left").pack(anchor="w")

    def _style_notebook(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=ACCENT2, foreground=MUTED,
                        font=BTN_F, padding=[12, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", TEXT)])

    def _btn(self, parent, text, cmd, big=False, secondary=False):
        bg = ACCENT if not secondary else ACCENT2
        f  = ("Segoe UI", 11, "bold") if big else BTN_F
        pad = (20, 10) if big else (12, 6)
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=TEXT, activebackground=TEXT,
                      activeforeground=BG, relief="flat",
                      font=f, padx=pad[0], pady=pad[1],
                      cursor="hand2", bd=0)
        b.bind("<Enter>", lambda e: b.config(bg=TEXT if not secondary else MUTED,
                                              fg=BG if not secondary else BG))
        b.bind("<Leave>", lambda e: b.config(bg=bg, fg=TEXT))
        return b

    # ── actions ---------------------------------------------------------------

    def _browse(self):
        d = filedialog.askdirectory()
        if d:
            self.dir_var.set(d)

    def _log(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    def _run(self):
        directory = self.dir_var.get().strip()
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("No directory", "Please select a valid directory first.")
            return

        tab = self._nb.index(self._nb.select())
        self._log(f"── Directory: {directory}")

        try:
            if tab == 0:
                self._log("── Operation: Capitalize filenames\n")
                run_capitalize(directory, self._log)

            elif tab == 1:
                prefix = self._prefix_add_var.get()
                if not prefix:
                    folder = os.path.basename(directory).replace(" ", "")
                    prefix = folder + "_"
                    self._log(f"── Using folder-name prefix: {prefix}")
                self._log(f"── Operation: Add prefix '{prefix}'\n")
                run_add_prefix(directory, prefix, self._log)

            elif tab == 2:
                prefix = self._prefix_rem_var.get()
                if not prefix:
                    messagebox.showerror("No prefix", "Please enter a prefix to remove.")
                    return
                self._log(f"── Operation: Remove prefix '{prefix}'\n")
                run_remove_prefix(directory, prefix, self._log)

        except Exception as exc:
            self._log(f"\n⚠ Error: {exc}")
            messagebox.showerror("Error", str(exc))

        self._log("─" * 50)


if __name__ == "__main__":
    app = FileRenamerApp()
    app.mainloop()