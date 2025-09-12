from datetime import datetime

import urwid
from .slurm import commands
from .ui.palettes import NORD_PALETTE
from .ui.widgets import ListFilterBox, LogPanel


def unhandled(key):
    if key in ("q", "Q"):
        raise urwid.ExitMainLoop()


def main():
    def export(jobs):
        with open("jobs.txt", "w") as o:
            for job in jobs:
                o.write(f"{job}\n")
        list_filter.open_pop_up(
            pop_up_type=ListFilterBox.MESSAGE_POPUP, message="Jobs exported succesfully"
        )

    jobs = commands.squeue()
    list_filter = ListFilterBox(jobs, title="JOBS")

    def update_partition_panel(loop, partition_text_ui):
        sinfo = commands.sinfo()
        sinfo_str = ""
        sinfo.sort(key=lambda x: x["total"], reverse=True)
        for partition in sinfo:
            sinfo_str += f"{partition['PARTITION'][:10]:10s} Alloc: {partition.get('alloc', '-'):>3} Idle: {partition.get('idle', 0):>3} Total:{partition.get('total', 0):>3}\n"

        sinfo_str += f"Last Update: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
        partition_text_ui.set_text(sinfo_str)
        loop.set_alarm_in(5, update_partition_panel, partition_text_ui)

    log_panel = LogPanel()
    partition_text_ui = urwid.Text("")
    partition_panel = urwid.LineBox(urwid.Filler(partition_text_ui), title="Partitions")
    columns = urwid.Columns(
        [
            ("weight", 2, log_panel),
            ("weight", 1, partition_panel),
        ]
    )

    pile = urwid.Pile([list_filter, (10, columns)])

    main_loop = urwid.MainLoop(
        urwid.AttrMap(pile, "background"),
        palette=NORD_PALETTE,
        unhandled_input=unhandled,
        pop_ups=True,
    )

    def refresh_jobs(dummy=None):
        jobs = commands.squeue()
        list_filter.update_data(jobs)

    def cancel_jobs(jobs):
        for job in jobs:
            commands.scancel(job["JOBID"])
        refresh_jobs()

    urwid.connect_signal(list_filter, "log", log_panel.log)

    list_filter.add_handler("w", "Export jobs to file", export)
    list_filter.add_handler("r", "Refresh Jobs", refresh_jobs)
    list_filter.add_handler("c", "Cancel Job", cancel_jobs, confirmation=True)

    main_loop.set_alarm_in(1, update_partition_panel, partition_text_ui)

    main_loop.run()


if __name__ == "__main__":
    main()
