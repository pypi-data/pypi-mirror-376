import urwid


# --------- HELPERS ----------
def is_selectable(w):
    # respeita wrappers (LineBox, AttrMap, etc.)
    bw = getattr(w, "base_widget", w)
    return bw.selectable()


def normalize_backtab(keys, raw):
    # alguns terminais mandam "backtab" em vez de "shift tab"
    return ["shift tab" if k == "backtab" else k for k in keys]


# --------- WIDGETS COM TAB ----------
class TabPile(urwid.Pile):
    def keypress(self, size, key):
        handled = super().keypress(size, key)
        if handled is None:
            return None
        cmd = urwid.command_map.get(key)
        if cmd in ("next selectable", "prev selectable"):
            step = 1 if cmd == "next selectable" else -1
            n = len(self.contents)
            curpos = self.focus_position
            pos = self.focus_position
            for _ in range(n - 1):  # evita loop infinito
                pos = (pos + step) % n
                w, _ = self.contents[pos]
                if is_selectable(w):
                    self.focus_position = pos
                    if curpos > pos:
                        return super().keypress(size, key)
                    return None
            return None
        return super().keypress(size, key)


class TabColumns(urwid.Columns):
    def keypress(self, size, key):
        # se ninguém tratou e for Tab/Shift-Tab, mude de coluna
        handled = super().keypress(size, key)
        if handled is None:
            return None

        cmd = urwid.command_map.get(key)
        if cmd in ("next selectable", "prev selectable"):
            step = 1 if cmd == "next selectable" else -1
            n = len(self.contents)
            curpos = self.focus_position
            pos = self.focus_position
            for _ in range(n - 1):
                pos = (pos + step) % n
                w, _ = self.contents[pos]
                if is_selectable(w):
                    self.set_focus_column(pos)
                    if step * (curpos - pos) > 0:
                        return super().keypress(size, key)
                    return None
            return None

        return super().keypress(size, key)
