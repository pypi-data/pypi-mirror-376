#!/usr/bin/env python3
"""
Test script to demonstrate the ListFilterBox confirmation functionality.

This script creates a ListFilterBox with sample data and adds handlers that
require user confirmation before executing their actions.
"""

import urwid
from lazyslurm.ui.widgets import ListFilterBox
from lazyslurm.ui.palettes import NORD_PALETTE


def main():
    """
    Entry point for the test application.

    This function creates a ListFilterBox with sample data and adds handlers
    with confirmation requirements to test the confirmation popup functionality.
    """

    def unhandled(key):
        if key in ("q", "Q"):
            raise urwid.ExitMainLoop()

    # Sample data for testing
    sample_data = [
        {"name": "John Doe", "age": 30, "department": "Engineering"},
        {"name": "Jane Smith", "age": 28, "department": "Marketing"},
        {"name": "Bob Johnson", "age": 35, "department": "Engineering"},
        {"name": "Alice Brown", "age": 32, "department": "Sales"},
        {"name": "Charlie Wilson", "age": 29, "department": "HR"},
    ]

    list_filter = ListFilterBox(
        sample_data,
        title="Employee Management System",
        column_key="name"
    )

    main_loop = urwid.MainLoop(
        urwid.AttrMap(list_filter, "background"),
        palette=NORD_PALETTE,
        unhandled_input=unhandled,
        pop_ups=True,
    )

    # Handler functions for testing
    def delete_employees(employees):
        """Delete selected employees (with confirmation)."""
        names = [emp["name"] for emp in employees]
        list_filter.open_pop_up(
            pop_up_type=ListFilterBox.MESSAGE_POPUP,
            message=f"Deleted employees: {', '.join(names)}"
        )
        print(f"DELETED: {names}")

    def promote_employees(employees):
        """Promote selected employees (with confirmation)."""
        names = [emp["name"] for emp in employees]
        list_filter.open_pop_up(
            pop_up_type=ListFilterBox.MESSAGE_POPUP,
            message=f"Promoted employees: {', '.join(names)}"
        )
        print(f"PROMOTED: {names}")

    def fire_employees(employees):
        """Fire selected employees (with confirmation)."""
        names = [emp["name"] for emp in employees]
        list_filter.open_pop_up(
            pop_up_type=ListFilterBox.MESSAGE_POPUP,
            message=f"Fired employees: {', '.join(names)}"
        )
        print(f"FIRED: {names}")

    def view_details(employees):
        """View employee details (no confirmation needed)."""
        for emp in employees:
            print(f"Employee: {emp}")

    def export_data(employees):
        """Export employee data (no confirmation needed)."""
        with open("employees.txt", "w") as f:
            for emp in employees:
                f.write(f"{emp}\n")
        list_filter.open_pop_up(
            pop_up_type=ListFilterBox.MESSAGE_POPUP,
            message="Employee data exported to employees.txt"
        )

    # Add handlers with different confirmation requirements
    list_filter.add_handler(
        "d",
        "Delete selected employees",
        delete_employees,
        confirmation=True  # Requires confirmation
    )

    list_filter.add_handler(
        "p",
        "Promote selected employees",
        promote_employees,
        confirmation=True  # Requires confirmation
    )

    list_filter.add_handler(
        "f",
        "Fire selected employees",
        fire_employees,
        confirmation=True  # Requires confirmation
    )

    list_filter.add_handler(
        "v",
        "View employee details",
        view_details,
        confirmation=False  # No confirmation needed
    )

    list_filter.add_handler(
        "e",
        "Export employee data",
        export_data,
        confirmation=False  # No confirmation needed
    )

    list_filter.main_loop = main_loop

    print("Employee Management System Test")
    print("=" * 40)
    print("Instructions:")
    print("- Use arrow keys or hjkl to navigate")
    print("- Press space/enter to select/deselect rows")
    print("- Press 'a' to select all, 'u' to unselect all")
    print("- Press 'd' to delete (requires confirmation)")
    print("- Press 'p' to promote (requires confirmation)")
    print("- Press 'f' to fire (requires confirmation)")
    print("- Press 'v' to view details (no confirmation)")
    print("- Press 'e' to export data (no confirmation)")
    print("- Press '?' for help")
    print("- Press 'q' to quit")
    print("=" * 40)

    main_loop.run()


if __name__ == "__main__":
    main()

