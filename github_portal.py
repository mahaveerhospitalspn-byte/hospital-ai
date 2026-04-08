"""
github_portal.py — Mahaveer Hospital AI
========================================
Run this on your Windows desktop machine.
It watches your Hospital_AI folder for any .py file changes
and pushes them to GitHub automatically (which triggers Render redeploy).

SETUP (one time):
  pip install watchdog gitpython tkinter

RUN:
  python github_portal.py
  OR double-click if you make a .bat shortcut
"""

import os
import sys
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime

# ── Try imports ───────────────────────────────────────────────────────────────
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_OK = True
except ImportError:
    WATCHDOG_OK = False

try:
    import git
    GIT_OK = True
except ImportError:
    GIT_OK = False

# ── Config — edit this path ───────────────────────────────────────────────────
DEFAULT_FOLDER = os.path.join(os.path.expanduser("~"), "Desktop", "Hospital_AI")

# Files to watch (extensions)
WATCH_EXTENSIONS = {".py", ".txt", ".yaml", ".toml", ".sql", ".csv", ".md"}

# Files to NEVER push (patient data, secrets)
IGNORE_PATTERNS = {
    "users.csv", "Patients_Data.csv", "Audit_Trail.csv",
    "notifications.csv", "OT_Register.csv", "DayCare_Register.csv",
    "hospital.db", "local.db", ".env",
}

# Cooldown: wait this many seconds after last change before pushing
DEBOUNCE_SECONDS = 8


# ═════════════════════════════════════════════════════════════════════════════
# FILE WATCHER
# ═════════════════════════════════════════════════════════════════════════════

class ChangeHandler(FileSystemEventHandler):

    def __init__(self, portal):
        self.portal = portal
        self._pending = False
        self._timer   = None

    def on_modified(self, event):
        if event.is_directory:
            return
        path = event.src_path
        fname = os.path.basename(path)
        ext   = os.path.splitext(fname)[1].lower()
        if ext not in WATCH_EXTENSIONS:
            return
        if fname in IGNORE_PATTERNS:
            return
        self.portal.log(f"📝 Changed: {fname}")
        self._schedule_push()

    def on_created(self, event):
        self.on_modified(event)

    def _schedule_push(self):
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(DEBOUNCE_SECONDS, self._do_push)
        self._timer.daemon = True
        self._timer.start()

    def _do_push(self):
        self.portal.push_to_github()


# ═════════════════════════════════════════════════════════════════════════════
# MAIN PORTAL WINDOW
# ═════════════════════════════════════════════════════════════════════════════

class GitHubPortal:

    def __init__(self, root):
        self.root      = root
        self.observer  = None
        self.watching  = False
        self.repo      = None

        root.title("🏥 Hospital AI — GitHub Push Portal")
        root.geometry("700x580")
        root.configure(bg="#f0f4f8")
        root.resizable(True, True)

        self._build_ui()
        self._check_dependencies()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        r = self.root

        # Header
        hdr = tk.Frame(r, bg="#1565C0", pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🏥  Mahaveer Hospital — GitHub Deploy Portal",
                 fg="white", bg="#1565C0",
                 font=("Segoe UI", 14, "bold")).pack()
        tk.Label(hdr, text="Auto-push code changes → GitHub → Render redeploy",
                 fg="#bbdefb", bg="#1565C0",
                 font=("Segoe UI", 9)).pack()

        # Folder row
        frm = tk.Frame(r, bg="#f0f4f8", pady=8, padx=12)
        frm.pack(fill="x")
        tk.Label(frm, text="📁 Folder:", bg="#f0f4f8",
                 font=("Segoe UI", 10)).pack(side="left")
        self.folder_var = tk.StringVar(value=DEFAULT_FOLDER)
        tk.Entry(frm, textvariable=self.folder_var, width=50,
                 font=("Consolas", 9)).pack(side="left", padx=6)
        tk.Button(frm, text="Browse", command=self._browse,
                  bg="#e3f2fd", relief="flat", padx=8).pack(side="left")

        # GitHub token row
        frm2 = tk.Frame(r, bg="#f0f4f8", padx=12)
        frm2.pack(fill="x")
        tk.Label(frm2, text="🔑 GitHub Token:", bg="#f0f4f8",
                 font=("Segoe UI", 10)).pack(side="left")
        self.token_var = tk.StringVar()
        self.token_entry = tk.Entry(frm2, textvariable=self.token_var,
                                    width=42, show="•", font=("Consolas", 9))
        self.token_entry.pack(side="left", padx=6)
        tk.Button(frm2, text="👁", command=self._toggle_token,
                  bg="#f0f4f8", relief="flat").pack(side="left")

        # Repo URL row
        frm3 = tk.Frame(r, bg="#f0f4f8", padx=12, pady=4)
        frm3.pack(fill="x")
        tk.Label(frm3, text="🔗 Repo URL:", bg="#f0f4f8",
                 font=("Segoe UI", 10)).pack(side="left")
        self.repo_var = tk.StringVar(
            value="https://github.com/YOUR_USERNAME/YOUR_REPO.git"
        )
        tk.Entry(frm3, textvariable=self.repo_var, width=50,
                 font=("Consolas", 9)).pack(side="left", padx=6)

        # Commit message row
        frm4 = tk.Frame(r, bg="#f0f4f8", padx=12, pady=4)
        frm4.pack(fill="x")
        tk.Label(frm4, text="💬 Commit msg:", bg="#f0f4f8",
                 font=("Segoe UI", 10)).pack(side="left")
        self.msg_var = tk.StringVar(value="Auto update from desktop")
        tk.Entry(frm4, textvariable=self.msg_var, width=45,
                 font=("Consolas", 9)).pack(side="left", padx=6)

        # Buttons
        btn_frm = tk.Frame(r, bg="#f0f4f8", pady=8, padx=12)
        btn_frm.pack(fill="x")

        self.watch_btn = tk.Button(
            btn_frm, text="▶  Start Watching",
            command=self._toggle_watch,
            bg="#1565C0", fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", padx=16, pady=6
        )
        self.watch_btn.pack(side="left", padx=(0, 8))

        tk.Button(
            btn_frm, text="🚀  Push Now",
            command=self.push_to_github,
            bg="#2e7d32", fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", padx=16, pady=6
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btn_frm, text="🔄  Git Status",
            command=self._show_status,
            bg="#e65100", fg="white",
            font=("Segoe UI", 10),
            relief="flat", padx=12, pady=6
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btn_frm, text="🧹  Clear Log",
            command=self._clear_log,
            bg="#607d8b", fg="white",
            font=("Segoe UI", 10),
            relief="flat", padx=12, pady=6
        ).pack(side="left")

        # Status bar
        self.status_var = tk.StringVar(value="⏸  Not watching")
        self.status_bar = tk.Label(
            r, textvariable=self.status_var,
            bg="#e3f2fd", fg="#1565C0",
            font=("Segoe UI", 10, "bold"),
            anchor="w", padx=12, pady=6
        )
        self.status_bar.pack(fill="x")

        # Log
        log_frm = tk.Frame(r, bg="#f0f4f8", padx=12, pady=4)
        log_frm.pack(fill="both", expand=True)
        tk.Label(log_frm, text="📋 Activity Log",
                 bg="#f0f4f8", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.log_box = scrolledtext.ScrolledText(
            log_frm, height=14, bg="#1a1a2e", fg="#00e676",
            font=("Consolas", 9), insertbackground="white",
            state="disabled"
        )
        self.log_box.pack(fill="both", expand=True)

        # Footer
        tk.Label(r,
                 text="⚠  Never push: users.csv, Patients_Data.csv, hospital.db  (already in .gitignore)",
                 bg="#fff3e0", fg="#e65100",
                 font=("Segoe UI", 8), anchor="w", padx=8, pady=4
        ).pack(fill="x", side="bottom")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _browse(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(initialdir=self.folder_var.get())
        if d:
            self.folder_var.set(d)

    def _toggle_token(self):
        current = self.token_entry.cget("show")
        self.token_entry.config(show="" if current == "•" else "•")

    def _clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete(1.0, tk.END)
        self.log_box.config(state="disabled")

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {msg}\n"
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, line)
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")

    def _set_status(self, msg, color="#1565C0"):
        self.status_var.set(msg)
        self.status_bar.config(fg=color)

    def _check_dependencies(self):
        missing = []
        if not WATCHDOG_OK:
            missing.append("watchdog")
        if not GIT_OK:
            missing.append("gitpython")
        if missing:
            self.log(f"⚠  Missing packages: {', '.join(missing)}")
            self.log(f"   Run:  pip install {' '.join(missing)}")
            messagebox.showwarning(
                "Missing Packages",
                f"Please install:\n\npip install {' '.join(missing)}\n\n"
                "Then restart this portal."
            )

    # ── Watch toggle ──────────────────────────────────────────────────────────
    def _toggle_watch(self):
        if self.watching:
            self._stop_watch()
        else:
            self._start_watch()

    def _start_watch(self):
        folder = self.folder_var.get().strip()
        if not os.path.isdir(folder):
            messagebox.showerror("Error", f"Folder not found:\n{folder}")
            return
        if not WATCHDOG_OK:
            messagebox.showerror("Error", "Install watchdog first:\npip install watchdog")
            return

        handler      = ChangeHandler(self)
        self.observer = Observer()
        self.observer.schedule(handler, folder, recursive=True)
        self.observer.start()
        self.watching = True

        self.watch_btn.config(text="⏹  Stop Watching", bg="#c62828")
        self._set_status(f"👁  Watching: {folder}", "#2e7d32")
        self.log(f"👁  Started watching: {folder}")
        self.log(f"   Will push {DEBOUNCE_SECONDS}s after last change")

    def _stop_watch(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        self.watching = False
        self.watch_btn.config(text="▶  Start Watching", bg="#1565C0")
        self._set_status("⏸  Stopped", "#607d8b")
        self.log("⏹  Watching stopped")

    # ── Show git status ───────────────────────────────────────────────────────
    def _show_status(self):
        folder = self.folder_var.get().strip()
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=folder, capture_output=True, text=True
            )
            lines = result.stdout.strip() or "✅ Nothing to commit — working tree clean"
            self.log("── Git Status ──")
            for l in lines.split("\n"):
                self.log(f"  {l}")
            self.log("────────────────")
        except Exception as e:
            self.log(f"❌ git status failed: {e}")

    # ── Push to GitHub ────────────────────────────────────────────────────────
    def push_to_github(self):
        folder  = self.folder_var.get().strip()
        token   = self.token_var.get().strip()
        repo_url = self.repo_var.get().strip()
        msg     = self.msg_var.get().strip() or "Auto update from desktop"

        if not os.path.isdir(folder):
            self.log(f"❌ Folder not found: {folder}")
            return

        if not token:
            self.log("❌ GitHub token required. Get one at github.com → Settings → Developer settings → Personal access tokens")
            messagebox.showerror("No Token",
                "Enter your GitHub Personal Access Token.\n\n"
                "Get one at:\ngithub.com → Settings → Developer settings\n→ Personal access tokens → Tokens (classic)\n\n"
                "Required scopes: repo (full control)"
            )
            return

        self._set_status("🚀  Pushing to GitHub...", "#e65100")
        self.log("── Pushing to GitHub ──")

        def _push():
            try:
                # Build authenticated URL
                if "github.com" in repo_url:
                    if repo_url.startswith("https://"):
                        auth_url = repo_url.replace(
                            "https://",
                            f"https://{token}@"
                        )
                    else:
                        auth_url = repo_url
                else:
                    auth_url = repo_url

                # Init git if needed
                git_dir = os.path.join(folder, ".git")
                if not os.path.isdir(git_dir):
                    self.log("  ℹ  No git repo found — initialising...")
                    subprocess.run(["git", "init"], cwd=folder,
                                   capture_output=True)
                    subprocess.run(["git", "remote", "add", "origin", auth_url],
                                   cwd=folder, capture_output=True)
                    self.log("  ✅ Git repo initialised")
                else:
                    # Update remote URL with token
                    subprocess.run(
                        ["git", "remote", "set-url", "origin", auth_url],
                        cwd=folder, capture_output=True
                    )

                # Stage all changes (respects .gitignore)
                r1 = subprocess.run(
                    ["git", "add", "."],
                    cwd=folder, capture_output=True, text=True
                )
                if r1.returncode != 0:
                    self.log(f"  ❌ git add failed: {r1.stderr}")
                    return

                # Check if anything to commit
                status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=folder, capture_output=True, text=True
                )
                if not status.stdout.strip():
                    self.log("  ℹ  No changes to push — already up to date")
                    self._set_status("✅  Up to date", "#2e7d32")
                    return

                # Count changed files
                changed = status.stdout.strip().split("\n")
                self.log(f"  📦 {len(changed)} file(s) changed:")
                for f in changed[:10]:
                    self.log(f"     {f.strip()}")
                if len(changed) > 10:
                    self.log(f"     ... and {len(changed)-10} more")

                # Commit
                ts_msg = f"{msg} [{datetime.now().strftime('%d-%m-%Y %H:%M')}]"
                r2 = subprocess.run(
                    ["git", "commit", "-m", ts_msg],
                    cwd=folder, capture_output=True, text=True
                )
                if r2.returncode != 0 and "nothing to commit" not in r2.stdout:
                    self.log(f"  ❌ Commit failed: {r2.stderr or r2.stdout}")
                    return
                self.log(f"  ✅ Committed: {ts_msg}")

                # Push
                r3 = subprocess.run(
                    ["git", "push", "-u", "origin", "main", "--force-with-lease"],
                    cwd=folder, capture_output=True, text=True
                )
                if r3.returncode == 0:
                    self.log("  ✅ Pushed to GitHub successfully!")
                    self.log("  🚀 Render will auto-redeploy in ~60 seconds")
                    self._set_status("✅  Pushed! Render redeploying...", "#2e7d32")
                else:
                    # Try with 'master' branch if 'main' failed
                    r3b = subprocess.run(
                        ["git", "push", "-u", "origin", "master", "--force-with-lease"],
                        cwd=folder, capture_output=True, text=True
                    )
                    if r3b.returncode == 0:
                        self.log("  ✅ Pushed to GitHub (master branch)")
                        self._set_status("✅  Pushed!", "#2e7d32")
                    else:
                        err = r3.stderr or r3b.stderr
                        self.log(f"  ❌ Push failed: {err}")
                        if "Authentication" in err or "403" in err:
                            self.log("  💡 Token may be expired or missing 'repo' scope")
                        elif "rejected" in err:
                            self.log("  💡 Try: git pull first, or check branch name")
                        self._set_status("❌  Push failed", "#c62828")

            except FileNotFoundError:
                self.log("❌ git not found — install Git from https://git-scm.com")
                messagebox.showerror("Git Not Found",
                    "Git is not installed or not in PATH.\n\n"
                    "Download from: https://git-scm.com/download/win"
                )
            except Exception as ex:
                self.log(f"❌ Unexpected error: {ex}")
                self._set_status("❌  Error", "#c62828")

            self.log("──────────────────────")

        # Run push in background thread so UI doesn't freeze
        threading.Thread(target=_push, daemon=True).start()


# ═════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()
    app  = GitHubPortal(root)

    def on_close():
        if app.observer:
            app.observer.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
