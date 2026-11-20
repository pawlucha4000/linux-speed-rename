"""Multi-Rename – GTK window in the style of Total Commander's multi-rename tool."""

from __future__ import annotations

import os
import re
import sys
from urllib.parse import unquote, urlparse

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk, Pango  # noqa: E402

from . import engine as E  # noqa: E402
from .i18n import _, help_text  # noqa: E402

APP_TITLE = _("Multi-Rename")


def _natural_key(s: str):
    return [int(t) if t.isdigit() else t.casefold() for t in re.split(r"(\d+)", s)]


def _to_path(arg: str) -> str:
    if arg.startswith("file://"):
        return unquote(urlparse(arg).path)
    return os.path.abspath(arg)


class MaskField:
    """Eine Eingabezeile mit Verlauf (Pulldown) – wie im Total Commander."""

    def __init__(self, history: list[str], default: str):
        self.combo = Gtk.ComboBoxText.new_with_entry()
        for item in history:
            self.combo.append_text(item)
        self.entry: Gtk.Entry = self.combo.get_child()
        self.entry.set_text(default)

    def insert(self, text: str) -> None:
        pos = self.entry.get_position()
        bounds = self.entry.get_selection_bounds()
        if bounds:
            self.entry.delete_text(*bounds)
            pos = bounds[0]
        new_pos = self.entry.insert_text(text, pos)
        self.entry.grab_focus_without_selecting()
        self.entry.set_position(new_pos)

    @property
    def text(self) -> str:
        return self.entry.get_text()


class RenameWindow(Gtk.Window):
    COL_OLD, COL_NEW, COL_NOTE, COL_DIR, COL_PATH, COL_COLOR = range(6)

    def __init__(self, paths: list[str]):
        super().__init__(title=APP_TITLE)
        self.set_default_size(1100, 640)
        self.set_icon_name("edit-find-replace")
        self.cfg = E.load_config()
        self.paths = sorted(paths, key=lambda p: _natural_key(os.path.basename(p)))
        self.entries: list[E.Entry] = []
        self._pending = False

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin=10)
        self.add(outer)

        top = Gtk.Box(spacing=8)
        outer.pack_start(top, False, False, 0)

        # --- Dateiname ---
        self.name = MaskField(self.cfg.get("name_mask", []), "[N]")
        name_buttons = [
            (_("[N] Name"), lambda *_: self.name.insert("[N]")),
            (_("[N#-#] Part"), lambda *_: self._pick_part("N", self.name)),
            (_("[C] Counter"), lambda *_: self.name.insert("[C]")),
            (_("[YMD] Date"), lambda *_: self.name.insert("[YMD]")),
            (_("[hms] Time"), lambda *_: self.name.insert("[hms]")),
            (_("[P] Folder"), lambda *_: self.name.insert("[P]")),
        ]
        top.pack_start(self._mask_frame(_("New file name"), self.name, name_buttons, 2), True, True, 0)

        # --- Erweiterung ---
        self.ext = MaskField(self.cfg.get("ext_mask", []), "[E]")
        ext_buttons = [
            (_("[E] Extension"), lambda *_: self.ext.insert("[E]")),
            (_("[E#-#] Part"), lambda *_: self._pick_part("E", self.ext)),
            (_("[C] Counter"), lambda *_: self.ext.insert("[C]")),
        ]
        top.pack_start(self._mask_frame(_("Extension"), self.ext, ext_buttons, 1), False, False, 0)

        # --- Suchen & Ersetzen ---
        top.pack_start(self._search_frame(), True, True, 0)

        # --- Zähler ---
        top.pack_start(self._counter_frame(), False, False, 0)

        # --- Sortierung ---
        sortbar = Gtk.Box(spacing=6)
        sortbar.pack_start(Gtk.Label(label=_("Order (sets the counter):")), False, False, 0)
        for label, key in ((_("by name"), "name"), (_("by date"), "date")):
            b = Gtk.Button(label=label)
            b.connect("clicked", self._sort, key)
            sortbar.pack_start(b, False, False, 0)
        sortbar.pack_start(Gtk.Label(label=_("or drag rows with the mouse")), False, False, 0)
        reset = Gtk.Button(label=_("Reset all"))
        reset.connect("clicked", self._reset)
        sortbar.pack_end(reset, False, False, 0)
        outer.pack_start(sortbar, False, False, 0)

        # --- Vorschau ---
        self.store = Gtk.ListStore(str, str, str, str, str, str)
        self.view = Gtk.TreeView(model=self.store)
        self.view.set_reorderable(True)
        self.store.connect("rows-reordered", lambda *_: self._on_reorder())
        self.store.connect("row-deleted", lambda *_: self._on_reorder())
        for title, col, width in ((_("Old name"), self.COL_OLD, 300), (_("New name"), self.COL_NEW, 300),
                                  (_("Note"), self.COL_NOTE, 170), (_("Folder"), self.COL_DIR, 220)):
            r = Gtk.CellRendererText()
            if col != self.COL_NOTE:
                r.set_property("ellipsize", Pango.EllipsizeMode.START if col == self.COL_DIR
                               else Pango.EllipsizeMode.MIDDLE)
            c = Gtk.TreeViewColumn(title, r, text=col)
            if col in (self.COL_NEW, self.COL_NOTE):
                c.add_attribute(r, "foreground", self.COL_COLOR)
            c.set_resizable(True)
            c.set_min_width(width)
            c.set_expand(col in (self.COL_OLD, self.COL_NEW))
            self.view.append_column(c)
        sw = Gtk.ScrolledWindow()
        sw.add(self.view)
        outer.pack_start(sw, True, True, 0)

        # --- Unten ---
        bottom = Gtk.Box(spacing=8)
        self.status = Gtk.Label(xalign=0)
        self.status.set_ellipsize(Pango.EllipsizeMode.END)
        bottom.pack_start(self.status, True, True, 0)
        help_btn = Gtk.Button(label=_("Help"))
        help_btn.connect("clicked", self._show_help)
        self.undo_btn = Gtk.Button(label=_("Undo"))
        self.undo_btn.connect("clicked", self._undo)
        self.start_btn = Gtk.Button(label=_("Rename"))
        self.start_btn.get_style_context().add_class("suggested-action")
        self.start_btn.connect("clicked", self._start)
        close_btn = Gtk.Button(label=_("Close"))
        close_btn.connect("clicked", lambda *_: self.close())
        for b in (help_btn, self.undo_btn, self.start_btn, close_btn):
            bottom.pack_start(b, False, False, 0)
        outer.pack_start(bottom, False, False, 0)

        for field in (self.name, self.ext, self.search, self.replace):
            field.entry.connect("changed", self._schedule)
        for w in (self.regex, self.once, self.include_ext):
            w.connect("toggled", self._schedule)
        self.case.connect("changed", self._schedule)
        for w in (self.c_start, self.c_step, self.c_digits):
            w.connect("value-changed", self._schedule)

        self.connect("key-press-event", self._on_key)
        self.name.entry.grab_focus()
        self._refresh()

    # ---------- Bausteine der Oberfläche ----------

    def _frame(self, title: str, child: Gtk.Widget) -> Gtk.Frame:
        frame = Gtk.Frame(label=title)
        child.set_margin_start(8)
        child.set_margin_end(8)
        child.set_margin_top(4)
        child.set_margin_bottom(8)
        frame.add(child)
        return frame

    def _mask_frame(self, title, field: MaskField, buttons, cols: int) -> Gtk.Frame:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.pack_start(field.combo, False, False, 0)
        grid = Gtk.Grid(column_spacing=6, row_spacing=6, column_homogeneous=True)
        for i, (label, cb) in enumerate(buttons):
            b = Gtk.Button(label=label)
            b.connect("clicked", cb)
            grid.attach(b, i % cols, i // cols, 1, 1)
        box.pack_start(grid, False, False, 0)
        return self._frame(title, box)

    def _search_frame(self) -> Gtk.Frame:
        grid = Gtk.Grid(column_spacing=6, row_spacing=6)
        self.search = MaskField(self.cfg.get("search", []), "")
        self.replace = MaskField(self.cfg.get("replace", []), "")
        self.search.combo.set_hexpand(True)
        grid.attach(Gtk.Label(label=_("Search for:"), xalign=0), 0, 0, 1, 1)
        grid.attach(self.search.combo, 1, 0, 1, 1)
        grid.attach(Gtk.Label(label=_("Replace with:"), xalign=0), 0, 1, 1, 1)
        grid.attach(self.replace.combo, 1, 1, 1, 1)
        opts = Gtk.Box(spacing=10)
        self.once = Gtk.CheckButton(label=_("only once"))
        self.include_ext = Gtk.CheckButton(label=_("also in extension"))
        self.regex = Gtk.CheckButton(label=_("Regular expression"))
        self.once.set_tooltip_text(_("Replace only the first occurrence"))
        self.regex.set_tooltip_text(_("For advanced users: treat the search text as a regular expression"))
        for w in (self.once, self.include_ext, self.regex):
            opts.pack_start(w, False, False, 0)
        grid.attach(opts, 0, 2, 2, 1)
        grid.attach(Gtk.Label(label=_("Case:"), xalign=0), 0, 3, 1, 1)
        self.case = Gtk.ComboBoxText()
        for opt in E.CASE_OPTIONS:
            self.case.append_text(opt)
        self.case.set_active(0)
        grid.attach(self.case, 1, 3, 1, 1)
        return self._frame(_("Search & Replace"), grid)

    def _counter_frame(self) -> Gtk.Frame:
        grid = Gtk.Grid(column_spacing=6, row_spacing=6)
        c = self.cfg.get("counter", {})
        self.c_start = Gtk.SpinButton.new_with_range(0, 10**9, 1)
        self.c_step = Gtk.SpinButton.new_with_range(-10**6, 10**6, 1)
        self.c_digits = Gtk.SpinButton.new_with_range(1, 12, 1)
        self.c_start.set_value(c.get("start", 1))
        self.c_step.set_value(c.get("step", 1))
        self.c_digits.set_value(c.get("digits", 1))
        for row, (label, w) in enumerate(((_("Start at:"), self.c_start), (_("Step:"), self.c_step),
                                          (_("Digits:"), self.c_digits))):
            grid.attach(Gtk.Label(label=label, xalign=0), 0, row, 1, 1)
            grid.attach(w, 1, row, 1, 1)
        self.c_digits.set_tooltip_text(_("3 digits gives 001, 002, 003 …"))
        return self._frame(_("Counter [C]"), grid)

    # ---------- Aktionen ----------

    def _pick_part(self, which: str, field: MaskField) -> None:
        sample = os.path.basename(self.paths[0]) if self.paths else _("Example name") + ".txt"
        base, ext = E.split_name(sample)
        text = base if which == "N" else ext
        dlg = Gtk.Dialog(title=_("Select part"), transient_for=self, modal=True)
        dlg.add_buttons(_("Cancel"), Gtk.ResponseType.CANCEL, _("Insert"), Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.OK)
        box = dlg.get_content_area()
        box.set_spacing(8)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.add(Gtk.Label(label=_("Select the part you want to keep with the mouse:"), xalign=0))
        entry = Gtk.Entry(text=text, editable=False, width_chars=max(len(text), 30))
        entry.set_activates_default(True)
        box.add(entry)
        to_end = Gtk.CheckButton(label=_("up to the end (even if other names are longer)"))
        from_right = Gtk.CheckButton(label=_("count from the end (the last characters)"))
        box.add(to_end)
        box.add(from_right)
        dlg.show_all()
        entry.select_region(0, 0)
        if dlg.run() == Gtk.ResponseType.OK:
            bounds = entry.get_selection_bounds()
            if bounds:
                a, b = bounds
                if from_right.get_active():
                    token = f"[{which}-{len(text) - a}]"
                elif to_end.get_active():
                    token = f"[{which}{a + 1}-]"
                elif b - a == 1:
                    token = f"[{which}{a + 1}]"
                else:
                    token = f"[{which}{a + 1}-{b}]"
                field.insert(token)
        dlg.destroy()

    def _settings(self) -> E.Settings:
        return E.Settings(
            name_mask=self.name.text, ext_mask=self.ext.text,
            search=self.search.text, replace=self.replace.text,
            regex=self.regex.get_active(), once=self.once.get_active(),
            include_ext=self.include_ext.get_active(), case=self.case.get_active(),
            counter_start=self.c_start.get_value_as_int(), counter_step=self.c_step.get_value_as_int(),
            counter_digits=self.c_digits.get_value_as_int(),
        )

    def _schedule(self, *_):
        if not self._pending:
            self._pending = True
            GLib.timeout_add(80, self._refresh)

    def _refresh(self):
        self._pending = False
        self.entries = E.compute(self.paths, self._settings())
        self._fill_store()
        n_err = sum(1 for e in self.entries if e.error)
        n_chg = sum(1 for e in self.entries if e.changed and not e.error)
        if n_err:
            self.status.set_markup("<span foreground='#c01c28'>%s</span>" % GLib.markup_escape_text(
                _("Conflicts: {n} – please adjust the mask.").format(n=n_err)))
        elif n_chg:
            self.status.set_text(_("Files to be renamed: {n} of {total}").format(n=n_chg, total=len(self.entries)))
        else:
            self.status.set_text(_("Files: {total} – no changes yet").format(total=len(self.entries)))
        self.start_btn.set_sensitive(n_chg > 0 and not n_err)
        self.undo_btn.set_sensitive(bool(E.load_journal()))
        return False

    def _fill_store(self):
        self._filling = True
        self.store.clear()
        for e in self.entries:
            color = "#c01c28" if e.error else None
            note = e.error or ("" if e.changed else _("unchanged"))
            self.store.append([e.old_name, e.new_name, note, e.directory, e.path, color])
        self._filling = False

    def _on_reorder(self):
        if getattr(self, "_filling", False):
            return
        new_order = [row[self.COL_PATH] for row in self.store]
        if len(new_order) == len(self.paths) and new_order != self.paths:
            self.paths = new_order
            self._schedule()

    def _sort(self, _btn, key):
        if key == "name":
            self.paths.sort(key=lambda p: _natural_key(os.path.basename(p)))
        else:
            self.paths.sort(key=lambda p: (os.path.getmtime(p) if os.path.lexists(p) else 0, p))
        self._refresh()

    def _reset(self, *_):
        self.name.entry.set_text("[N]")
        self.ext.entry.set_text("[E]")
        self.search.entry.set_text("")
        self.replace.entry.set_text("")
        for w in (self.regex, self.once, self.include_ext):
            w.set_active(False)
        self.case.set_active(0)
        self.c_start.set_value(1)
        self.c_step.set_value(1)
        self.c_digits.set_value(1)

    def _remember(self):
        s = self._settings()
        for key, value, field in (("name_mask", s.name_mask, self.name), ("ext_mask", s.ext_mask, self.ext),
                                  ("search", s.search, self.search), ("replace", s.replace, self.replace)):
            before = self.cfg.get(key, [])
            E.remember(self.cfg, key, value)
            if self.cfg.get(key, []) != before:
                text = field.entry.get_text()
                field.combo.remove_all()
                for item in self.cfg[key]:
                    field.combo.append_text(item)
                field.entry.set_text(text)
        self.cfg["counter"] = {"start": s.counter_start, "step": s.counter_step, "digits": s.counter_digits}
        try:
            E.save_config(self.cfg)
        except OSError:
            pass

    def _start(self, *_):
        self.entries = E.compute(self.paths, self._settings())
        if E.has_errors(self.entries):
            self._refresh()
            return
        try:
            done = E.execute(self.entries)
        except Exception as exc:  # noqa: BLE001
            self._error(_("Renaming failed. Nothing was changed."), str(exc))
            self._refresh()
            return
        E.save_journal(done)
        self._remember()
        mapping = dict(done)
        self.paths = [mapping.get(p, p) for p in self.paths]
        self._refresh()
        self.status.set_text(_("Files renamed: {n}. “Undo” restores the old names.").format(n=len(done)))

    def _undo(self, *_):
        try:
            reverted = E.undo_last()
        except Exception as exc:  # noqa: BLE001
            self._error(_("Undo is not possible."), str(exc))
            return
        mapping = dict(reverted)
        self.paths = [mapping.get(p, p) for p in self.paths]
        self._refresh()
        self.status.set_text(_("Files restored to their old names: {n}").format(n=len(reverted)))

    def _error(self, title: str, detail: str):
        dlg = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.ERROR,
                                buttons=Gtk.ButtonsType.OK, text=title)
        dlg.format_secondary_text(detail)
        dlg.run()
        dlg.destroy()

    def _show_help(self, *_):
        dlg = Gtk.Dialog(title=_("Help") + " – " + APP_TITLE, transient_for=self, modal=True)
        dlg.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        dlg.set_default_size(620, 560)
        label = Gtk.Label(xalign=0, yalign=0, wrap=True, selectable=True)
        label.set_markup(help_text())
        sw = Gtk.ScrolledWindow(margin=12)
        sw.add(label)
        dlg.get_content_area().pack_start(sw, True, True, 0)
        dlg.show_all()
        dlg.run()
        dlg.destroy()

    def _on_key(self, _w, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        if event.keyval == Gdk.KEY_F1:
            self._show_help()
            return True
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and event.state & Gdk.ModifierType.CONTROL_MASK:
            if self.start_btn.get_sensitive():
                self._start()
            return True
        return False


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    paths = [_to_path(a) for a in args if a and not a.startswith("--")]
    paths = [p for p in dict.fromkeys(paths) if os.path.lexists(p)]
    if not paths:
        dlg = Gtk.FileChooserDialog(title=_("Choose files to rename"), action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons(_("Cancel"), Gtk.ResponseType.CANCEL, _("Open"), Gtk.ResponseType.OK)
        dlg.set_select_multiple(True)
        if dlg.run() == Gtk.ResponseType.OK:
            paths = dlg.get_filenames()
        dlg.destroy()
        if not paths:
            return 0
    win = RenameWindow(paths)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
