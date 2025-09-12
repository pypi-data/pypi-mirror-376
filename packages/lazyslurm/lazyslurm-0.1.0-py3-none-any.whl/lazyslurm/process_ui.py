import getpass
import urwid
from process import commands
from ui.palettes import NORD_PALETTE
from ui.widgets import ListFilterBox, LogPanel, log, ConfirmationPopup


def unhandled(key):
    if key in ("q", "Q"):
        raise urwid.ExitMainLoop()


def main():
    processes = commands.get_processes(user=getpass.getuser())
    list_filter = ListFilterBox(processes, title="Processes", column_key="pid")

    log_panel = LogPanel()

    pile = urwid.Pile([list_filter, (10, log_panel)])

    main_loop = urwid.MainLoop(
        urwid.AttrMap(pile, "background"),
        palette=NORD_PALETTE,
        unhandled_input=unhandled,
        pop_ups=True,
    )

    def kill_processes(processes):
        for process in processes:
            log(list_filter, f"Killing process {process['pid']}")
            commands.kill_process(process["pid"])

    def refresh_processes(processes):
        log(list_filter, "Refreshing processes")
        updated_processes = commands.get_processes(user=getpass.getuser())
        list_filter.update_data(updated_processes)

    list_filter.add_handler("c", "Cancel Process (kill)", kill_processes, True)
    list_filter.add_handler("r", "Refresh processes", refresh_processes)

    urwid.connect_signal(list_filter, "log", log_panel.log)

    main_loop.run()


if __name__ == "__main__":
    main()
