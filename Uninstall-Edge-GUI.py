"""LokiBytes Edge Uninstaller - GUI front-end for Uninstall-Edge.ps1.

Wraps the PowerShell uninstall script in a themed customtkinter GUI matching
the LokiBytes Deep Matte Black + Metallic Gold visual style used across the
LokiBytes app suite.
"""
from __future__ import annotations

import ctypes
import queue
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

APP_VERSION = "1.0.1"
DONATE_URL = "https://paypal.me/ITgamer"

# When frozen by PyInstaller, bundled data files live under sys._MEIPASS
# (a temp dir extracted for the life of the process) instead of next to the
# script, so resolve the base dir accordingly.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

PS1_PATH = BASE_DIR / "Uninstall-Edge.ps1"
LOGO_PATH = BASE_DIR / "resources" / "lokibytes_logo.png"
ABOUT_LOGO_PATH = BASE_DIR / "resources" / "LokiBytes_About.png"
ICON_PATH = BASE_DIR / "resources" / "lokibytes_icon.ico"

REGIONS = {
    "DE - Germany": "DE",
    "FR - France": "FR",
    "NL - Netherlands": "NL",
    "IE - Ireland": "IE",
    "IT - Italy": "IT",
    "ES - Spain": "ES",
}


class Palette:
    BLACK = "#0D0D0D"
    CHARCOAL = "#1A1A1A"
    CHARCOAL_LIGHT = "#242424"
    CHARCOAL_BORDER = "#2A2A2A"
    GOLD = "#D4AF37"
    GOLD_HOVER = "#E6C35C"
    TEXT_PRIMARY = "#F5F5F0"
    TEXT_SECONDARY = "#A8A8A0"
    TEXT_ON_GOLD = "#0D0D0D"
    ERROR = "#C0392B"
    ERROR_HOVER = "#A93226"
    CARD_CREAM = "#EDE8D5"


_FONT_SPECS = {
    "subheading": {"family": "Segoe UI", "size": 16, "weight": "bold"},
    "body": {"family": "Segoe UI", "size": 13},
    "body_bold": {"family": "Segoe UI", "size": 13, "weight": "bold"},
    "small": {"family": "Segoe UI", "size": 11},
    "mono": {"family": "Consolas", "size": 12},
}
_font_cache: dict[str, ctk.CTkFont] = {}


def get_font(name: str) -> ctk.CTkFont:
    if name not in _font_cache:
        _font_cache[name] = ctk.CTkFont(**_FONT_SPECS[name])
    return _font_cache[name]


_BUTTON_STYLES = {
    "primary": dict(fg_color=Palette.GOLD, hover_color=Palette.GOLD_HOVER, text_color=Palette.TEXT_ON_GOLD),
    "secondary": dict(
        fg_color=Palette.CHARCOAL, hover_color=Palette.CHARCOAL_LIGHT, text_color=Palette.TEXT_PRIMARY,
        border_color=Palette.GOLD, border_width=1,
    ),
    "danger": dict(fg_color=Palette.ERROR, hover_color=Palette.ERROR_HOVER, text_color=Palette.TEXT_PRIMARY),
    "ghost": dict(fg_color="transparent", hover_color=Palette.CHARCOAL_LIGHT, text_color=Palette.GOLD),
}


def gold_button(master, text, command=None, variant="primary", **kwargs):
    style = dict(_BUTTON_STYLES[variant])
    style.update(kwargs)
    return ctk.CTkButton(master, text=text, command=command, corner_radius=6, font=get_font("body_bold"), **style)


def divider(master, **kwargs):
    line = ctk.CTkFrame(master, height=1, fg_color=Palette.CHARCOAL_BORDER, **kwargs)
    line.pack_propagate(False)
    return line


def load_ctk_image(path: Path, max_size: tuple[int, int]) -> ctk.CTkImage:
    img = Image.open(path)
    img.thumbnail(max_size, Image.LANCZOS)
    return ctk.CTkImage(light_image=img, dark_image=img, size=img.size)


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> None:
    script_path = str(Path(__file__).resolve())
    python_exe = Path(sys.executable)
    pythonw = python_exe.with_name("pythonw.exe")
    exe = str(pythonw) if pythonw.exists() else str(python_exe)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, f'"{script_path}"', None, 1)


class AboutDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("About LokiBytes Edge Uninstaller")
        self.geometry("460x460")
        self.resizable(False, False)
        self.configure(fg_color=Palette.BLACK)
        # CTkToplevel unconditionally resets its titlebar icon to CustomTkinter's
        # own default 200ms after construction, so ours must be set after that
        # or it gets silently overwritten.
        self.after(250, self._set_icon)
        self.transient(master)
        self.after(50, self.grab_set)
        self._build()

    def _set_icon(self) -> None:
        try:
            self.iconbitmap(str(ICON_PATH))
        except Exception:
            pass

    def _build(self) -> None:
        ctk.CTkFrame(self, fg_color="transparent", height=16).pack()

        logo_card = ctk.CTkFrame(
            self, fg_color=Palette.CARD_CREAM, corner_radius=6, border_width=2, border_color=Palette.GOLD,
        )
        logo_card.pack()
        try:
            img = load_ctk_image(ABOUT_LOGO_PATH, (220, 220))
            ctk.CTkLabel(logo_card, image=img, text="", fg_color="transparent").pack(padx=12, pady=12)
        except Exception:
            ctk.CTkLabel(
                logo_card, text="LB", text_color=Palette.GOLD, font=get_font("subheading"), fg_color="transparent",
            ).pack(padx=24, pady=24)

        ctk.CTkLabel(
            self, text="LokiBytes Edge Uninstaller", text_color=Palette.GOLD, font=get_font("subheading"),
        ).pack(pady=(12, 0))

        ctk.CTkLabel(
            self, text=f"Version {APP_VERSION}", text_color=Palette.TEXT_SECONDARY, font=get_font("small"),
        ).pack(pady=(2, 0))

        divider(self).pack(fill="x", padx=60, pady=16)

        ctk.CTkLabel(
            self,
            text=(
                "LokiBytes Edge Uninstaller fully removes Microsoft Edge (Chromium)\n"
                "from Windows -- including the EdgeUpdate service, scheduled tasks,\n"
                "leftover files, shortcuts, and registry keys -- by temporarily\n"
                "unlocking the EEA/DMA uninstall gate Microsoft already exposes to\n"
                "European users, then blocks Edge from silently reinstalling itself."
            ),
            text_color=Palette.TEXT_SECONDARY, font=get_font("body"), justify="center",
        ).pack(padx=24)

        divider(self).pack(fill="x", padx=60, pady=16)

        ctk.CTkLabel(
            self, text="© 2026 LokiBytes. All rights reserved.",
            text_color=Palette.TEXT_SECONDARY, font=get_font("small"),
        ).pack()

        gold_button(self, text="Close", variant="secondary", command=self.destroy, width=110).pack(pady=(16, 20))


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._proc: subprocess.Popen | None = None
        self._output_queue: queue.Queue = queue.Queue()

        self.title("LokiBytes Edge Uninstaller")
        self.geometry("640x640")
        self.resizable(False, False)
        self.configure(fg_color=Palette.BLACK)
        try:
            self.iconbitmap(str(ICON_PATH))
        except Exception:
            pass
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_header()
        self._build_body()
        self._build_footer()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=Palette.CHARCOAL, corner_radius=0, height=72)
        header.pack(fill="x")
        header.pack_propagate(False)

        try:
            img = load_ctk_image(LOGO_PATH, (48, 48))
            ctk.CTkLabel(header, image=img, text="").pack(side="left", padx=(16, 12), pady=12)
        except Exception:
            pass

        text_frame = ctk.CTkFrame(header, fg_color="transparent")
        text_frame.pack(side="left", pady=14)
        ctk.CTkLabel(
            text_frame, text="LokiBytes Edge Uninstaller",
            text_color=Palette.GOLD, font=get_font("subheading"), anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            text_frame, text="Fully remove Microsoft Edge (Chromium) from Windows",
            text_color=Palette.TEXT_SECONDARY, font=get_font("small"), anchor="w",
        ).pack(anchor="w")

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color=Palette.BLACK, corner_radius=0)
        body.pack(fill="both", expand=True, padx=24, pady=18)

        ctk.CTkLabel(
            body, text="Temporary EEA region (required for Edge's uninstall gate):",
            text_color=Palette.TEXT_SECONDARY, font=get_font("body"), anchor="w",
        ).pack(anchor="w")

        self._region_var = ctk.StringVar(value=next(iter(REGIONS)))
        self._region_menu = ctk.CTkOptionMenu(
            body, values=list(REGIONS.keys()), variable=self._region_var, width=220,
            fg_color=Palette.CHARCOAL, button_color=Palette.GOLD, button_hover_color=Palette.GOLD_HOVER,
            text_color=Palette.TEXT_PRIMARY, dropdown_fg_color=Palette.CHARCOAL,
            dropdown_hover_color=Palette.CHARCOAL_LIGHT, dropdown_text_color=Palette.TEXT_PRIMARY,
            font=get_font("body"),
        )
        self._region_menu.pack(anchor="w", pady=(6, 14))

        self._revert_var = ctk.BooleanVar(value=False)
        self._revert_check = ctk.CTkCheckBox(
            body, text="Revert region back to original automatically after uninstalling",
            variable=self._revert_var, text_color=Palette.TEXT_SECONDARY, font=get_font("body"),
            fg_color=Palette.GOLD, hover_color=Palette.GOLD_HOVER, checkmark_color=Palette.TEXT_ON_GOLD,
            border_color=Palette.GOLD,
        )
        self._revert_check.pack(anchor="w", pady=(0, 14))

        ctk.CTkLabel(
            body,
            text=(
                "This will force-uninstall Microsoft Edge, remove EdgeUpdate services/tasks, "
                "delete leftover files & registry keys, and restart Explorer twice. A reboot "
                "is recommended afterward."
            ),
            text_color=Palette.ERROR, font=get_font("small"), wraplength=580, justify="left", anchor="w",
        ).pack(anchor="w", fill="x", pady=(0, 14))

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(anchor="w", pady=(0, 14))
        self._run_btn = gold_button(
            btn_row, text="Uninstall Edge", variant="danger", command=self._on_run, width=150, height=34,
        )
        self._run_btn.pack(side="left", padx=(0, 8))
        gold_button(
            btn_row, text="Close", variant="secondary", command=self._on_close, width=100, height=34,
        ).pack(side="left")

        self._progress = ctk.CTkProgressBar(
            body, mode="indeterminate", fg_color=Palette.CHARCOAL_BORDER, progress_color=Palette.GOLD, height=8,
        )
        self._progress.pack(fill="x", pady=(0, 8))
        self._progress.set(0)

        self._status_lbl = ctk.CTkLabel(
            body, text="Ready.", text_color=Palette.TEXT_SECONDARY, font=get_font("small"), anchor="w",
        )
        self._status_lbl.pack(anchor="w", pady=(0, 8))

        self._output = ctk.CTkTextbox(
            body, fg_color=Palette.CHARCOAL, text_color=Palette.TEXT_PRIMARY, font=get_font("mono"),
            border_width=1, border_color=Palette.GOLD, wrap="none",
        )
        self._output.pack(fill="both", expand=True)
        self._output.configure(state="disabled")

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color=Palette.CHARCOAL, corner_radius=0, height=46)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        divider(footer).pack(fill="x")

        row = ctk.CTkFrame(footer, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=16)
        gold_button(row, text="About", variant="ghost", command=self._on_about, width=80, height=30).pack(
            side="left", pady=8
        )
        gold_button(
            row, text="Donate via PayPal", variant="ghost", command=self._on_donate, width=180, height=30,
        ).pack(side="right", pady=8)

    def _append_output(self, text: str) -> None:
        self._output.configure(state="normal")
        self._output.insert("end", text if text.endswith("\n") else text + "\n")
        self._output.see("end")
        self._output.configure(state="disabled")

    def _set_running(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        self._run_btn.configure(state=state)
        self._region_menu.configure(state=state)
        self._revert_check.configure(state=state)
        if running:
            self._progress.start()
        else:
            self._progress.stop()
        self._status_lbl.configure(text="Uninstalling Edge... please wait." if running else "Ready.")

    def _on_run(self) -> None:
        if not messagebox.askyesno(
            "Confirm Uninstall",
            "This will permanently uninstall Microsoft Edge and remove its leftover "
            "files, services, and registry keys. Continue?",
        ):
            return

        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.configure(state="disabled")
        self._set_running(True)

        region_code = REGIONS[self._region_var.get()]
        args = [
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(PS1_PATH), "-TempRegion", region_code,
        ]
        if self._revert_var.get():
            args.append("-RevertRegionAfter")

        threading.Thread(target=self._run_worker, args=(args,), daemon=True).start()
        self.after(150, self._poll_queue)

    def _run_worker(self, args: list[str]) -> None:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        try:
            self._proc = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, startupinfo=startupinfo,
            )
            for line in iter(self._proc.stdout.readline, ""):
                self._output_queue.put(("line", line.rstrip("\n")))
            self._proc.wait()
            self._output_queue.put(("done", self._proc.returncode))
        except Exception as exc:
            self._output_queue.put(("line", f"ERROR: {exc}"))
            self._output_queue.put(("done", 1))
        finally:
            self._proc = None

    def _poll_queue(self) -> None:
        finished = False
        try:
            while True:
                kind, payload = self._output_queue.get_nowait()
                if kind == "line":
                    self._append_output(payload)
                elif kind == "done":
                    finished = True
        except queue.Empty:
            pass

        if finished:
            self._set_running(False)
            messagebox.showinfo(
                "LokiBytes Edge Uninstaller",
                "Edge uninstall finished. A reboot is recommended to fully clear leftover handles/services.",
            )
        else:
            self.after(150, self._poll_queue)

    def _on_about(self) -> None:
        AboutDialog(self)

    def _on_donate(self) -> None:
        webbrowser.open(DONATE_URL)

    def _on_close(self) -> None:
        if self._proc is not None:
            try:
                self._proc.terminate()
            except Exception:
                pass
        self.destroy()


def main() -> None:
    if not is_admin():
        relaunch_as_admin()
        return

    if not PS1_PATH.exists():
        messagebox.showerror(
            "LokiBytes Edge Uninstaller",
            "Could not find Uninstall-Edge.ps1 next to this GUI script.",
        )
        return

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    MainWindow().mainloop()


if __name__ == "__main__":
    main()
