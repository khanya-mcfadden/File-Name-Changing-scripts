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

# ── Improved Prefix Removal Engine ───────────────────────────────────────────

def run_remove_prefix(directory, pattern_input, log):
    renamed = 0
    skipped = 0

    bracket_match = re.search(r'\((\d+)\)', pattern_input)

    use_dynamic_count = False
    remove_count = 0
    base_pattern = pattern_input

    if bracket_match:
        use_dynamic_count = True
        remove_count = int(bracket_match.group(1))
        base_pattern = pattern_input[:bracket_match.start()]
        log(f"Pattern mode: Dynamic removal")
        log(f"Base match: '{base_pattern}' | Remove next {remove_count} characters")

    regex_mode = False
    compiled_regex = None

    try:
        compiled_regex = re.compile(base_pattern)
        regex_mode = True
    except re.error:
        regex_mode = False

    for filename in os.listdir(directory):
        full_path = os.path.join(directory, filename)

        if not os.path.isfile(full_path):
            continue

        original_name = filename
        new_name = filename
        matched_text = None

        if use_dynamic_count:
            if base_pattern:
                if filename.startswith(base_pattern):
                    matched_text = base_pattern
                    start = len(base_pattern)
                    new_name = filename[start + remove_count:]
            else:
                matched_text = "(start)"
                new_name = filename[remove_count:]

        elif regex_mode:
            match = compiled_regex.match(filename)
            if match:
                matched_text = match.group(0)
                new_name = filename[len(matched_text):]

        else:
            if filename.startswith(pattern_input):
                matched_text = pattern_input
                new_name = filename[len(pattern_input):]

        if new_name == original_name:
            continue

        new_path = os.path.join(directory, new_name)

        if os.path.exists(new_path) and new_path.lower() != full_path.lower():
            log(f"Skipped (collision): {original_name}")
            skipped += 1
            continue

        temp = full_path + ".__temp__"
        os.rename(full_path, temp)
        os.rename(temp, new_path)

        removed_chars = len(original_name) - len(new_name)

        log(
f"""Original: {original_name}
Pattern Matched: {matched_text}
Characters Removed: {removed_chars}
Result: {new_name}
"""
        )

        renamed += 1

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

    def _build_ui(self):
        hdr = tk.Frame(self, bg=ACCENT2, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="File Renamer Suite", font=TITLE_F,
                 bg=ACCENT2, fg=TEXT).pack()
        tk.Label(hdr, text="Capitalize · Add Prefix · Remove Prefix",
                 font=("Segoe UI", 10), bg=ACCENT2, fg=MUTED).pack()

        body = tk.Frame(self, bg=BG, padx=24, pady=16)
        body.pack(fill="both", expand=True)

        dir_frame = tk.Frame(body, bg=BG)
        dir_frame.pack(fill="x", pady=(0, 14))
        tk.Label(dir_frame, text="Directory", font=LABEL_F,
                 bg=BG, fg=MUTED, width=12, anchor="w").pack(side="left")
        self.dir_var = tk.StringVar()
        tk.Entry(dir_frame, textvariable=self.dir_var,
                 font=MONO, bg=PANEL, fg=TEXT,
                 insertbackground=TEXT, relief="flat",
                 highlightthickness=1).pack(side="left", fill="x", expand=True, padx=(0,8))
        tk.Button(dir_frame, text="Browse…", command=self._browse).pack(side="left")

        nb = ttk.Notebook(body)
        nb.pack(fill="x", pady=(0, 14))

        self.tab_cap  = tk.Frame(nb, bg=PANEL, padx=12, pady=12)
        self.tab_add  = tk.Frame(nb, bg=PANEL, padx=12, pady=12)
        self.tab_rem  = tk.Frame(nb, bg=PANEL, padx=12, pady=12)
        nb.add(self.tab_cap, text="Capitalize")
        nb.add(self.tab_add, text="Add Prefix")
        nb.add(self.tab_rem, text="Remove Prefix")

        self._prefix_add_var = tk.StringVar()
        self._prefix_rem_var = tk.StringVar()

        tk.Entry(self.tab_add, textvariable=self._prefix_add_var).pack(fill="x")
        tk.Entry(self.tab_rem, textvariable=self._prefix_rem_var).pack(fill="x")

        run_frame = tk.Frame(body, bg=BG)
        run_frame.pack(fill="x", pady=(0, 12))
        tk.Button(run_frame, text="Run", command=self._run).pack(side="right")

        self.log_box = scrolledtext.ScrolledText(body, height=12)
        self.log_box.pack(fill="both", expand=True)

        self._nb = nb

    def _browse(self):
        d = filedialog.askdirectory()
        if d:
            self.dir_var.set(d)

    def _log(self, msg):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    def _run(self):
        directory = self.dir_var.get().strip()
        if not directory:
            return

        tab = self._nb.index(self._nb.select())

        if tab == 0:
            run_capitalize(directory, self._log)
        elif tab == 1:
            prefix = self._prefix_add_var.get()
            run_add_prefix(directory, prefix, self._log)
        elif tab == 2:
            pattern = self._prefix_rem_var.get()
            run_remove_prefix(directory, pattern, self._log)

if __name__ == "__main__":
    app = FileRenamerApp()
    app.mainloop()