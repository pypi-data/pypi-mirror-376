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
        cmd = urwid.command_map.get(key)
        if cmd in ("next selectable", "prev selectable"):
            step = 1 if cmd == "next selectable" else -1
            n = len(self.contents)
            pos = self.focus_position
            for _ in range(n - 1):  # evita loop infinito
                pos = (pos + step) % n
                w, _ = self.contents[pos]
                if is_selectable(w):
                    self.focus_position = pos
                    return None
            return None
        return super().keypress(size, key)


class TabColumns(urwid.Columns):
    def keypress(self, size, key):
        # tente deixar o filho atual tratar primeiro
        # se ninguém tratou e for Tab/Shift-Tab, mude de coluna
        cmd = urwid.command_map.get(key)
        if cmd in ("next selectable", "prev selectable"):
            step = 1 if cmd == "next selectable" else -1
            n = len(self.contents)
            pos = self.focus_position
            for _ in range(n - 1):
                pos = (pos + step) % n
                w, _ = self.contents[pos]
                if is_selectable(w):
                    self.set_focus_column(pos)
                    return None
            return None
        else:
            return super().keypress(size, key)


# --------- SUA UI (quase igual) ----------
menu = urwid.ListBox(
    urwid.SimpleFocusListWalker(
        [
            urwid.Button("Abrir"),
            urwid.Button("Salvar"),
            urwid.Button("Sair"),
        ]
    )
)

right_top = urwid.Edit("Nome: ")
right_bottom = urwid.Edit("E-mail: ")

right_panel = TabPile(
    [
        urwid.LineBox(right_top, title="Topo"),
        urwid.LineBox(right_bottom, title="Base"),
    ]
)

root = TabColumns(
    [
        ("weight", 1, urwid.LineBox(menu, title="Menu")),
        ("weight", 2, right_panel),
    ]
)

loop = urwid.MainLoop(
    root,
    palette=[("reveal focus", "black", "light gray", "standout")],
    input_filter=normalize_backtab,  # suporte a Shift-Tab em terminais "teimosos"
)
loop.run()
