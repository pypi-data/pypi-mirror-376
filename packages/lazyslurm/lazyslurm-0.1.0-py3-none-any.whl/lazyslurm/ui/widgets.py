# Reusable UI widgets for curConfirmationPopup
import os
import re
from collections import OrderedDict
from datetime import datetime

import urwid

from .popups import ConfirmationPopup, PopUpDialog, FilterPopup
from .palettes import NORD_PALETTE
from .tab_widgets import TabPile, TabColumns


def log(widget, message):
    urwid.emit_signal(widget, "log", message)


class LogPanel(urwid.LineBox):
    def __init__(self):
        self.text_ui = urwid.Text("")
        super().__init__(self.text_ui, title="Log")

    def log(self, message):
        date = datetime.now().strftime("%H:%m:%S - %Y-%m-%d")
        self.text_ui.set_text(self.text_ui.get_text()[0] + f"{date}: {message}\n")


class ListFilterBox(urwid.PopUpLauncher):
    """
    A reusable UI widget for curses-based applications.

    ListFilterBox is a specialized UI component that displays
    tabular data in a selectable list format, with features for
    filtering, selecting, and performing actions on rows.

    Attributes:
        main_loop: The urwid main loop controlling the UI rendering.
        handlers: A dictionary linking keys to their respective actions.
        columns_size: A dictionary defining the layout and column width of the table.
        items: The data to be displayed in the table as a list of dictionaries.
        selected_buttons: A set tracking currently selected rows.
    """

    signals = ["log"]

    HELP_POPUP = "HELP_POPUP"
    MESSAGE_POPUP = "MESSAGE_POPUP"
    FILTER_POPUP = "FILTER_POPUP"
    CONFIRMATION_POPUP = "CONFIRMATION_POPUP"

    def open_pop_up(self, **kwargs):
        self._pop_up_params = kwargs
        super().open_pop_up()

    def __init__(self, items, title="", column_key=None):
        """
        Initialize the ListFilterBox with a given list of dictionaries and an optional title.

        Args:
            items (list): The data to be displayed in the table, represented as a list of dictionaries.
            title (str): The title to display on the top of the ListFilterBox.

        Attributes:
            handlers: A dictionary mapping keys to their respective actions and descriptions.
            columns_size: A dictionary defining the layout and column widths of the table.
            items: The data displayed in the table as a list of dictionaries.
            selected_buttons: A set tracking currently selected rows.
            column_key: An optional key used to uniquely identify rows for selection and deselection.
        """
        self.handlers = OrderedDict()
        self.columns_size = OrderedDict()
        self.original_items = items  # Keep original data for filtering
        self.items = items
        self.selected_buttons = {}  # Attribute to track selected buttons
        self.column_key = column_key
        self.current_filters = {}  # Track current filter criteria
        self.pending_action = None  # Store pending action for confirmation
        self.pending_items = None  # Store items for pending action
        body = self._construct_body(items)
        self.list_walker = urwid.SimpleFocusListWalker(body)

        self._pop_up_params = None
        self.list_box = urwid.ListBox(self.list_walker)

        # Create footer
        self.footer = urwid.Text("", align="center")

        # Create pile with list_box and footer
        pile = urwid.Pile(
            [
                ("weight", 1, self.list_box),
                ("pack", urwid.AttrMap(self.footer, "footer")),
            ]
        )

        super().__init__(urwid.LineBox(pile, title=title))

    def _current_selected_count(self):
        """
        Return the number of currently selected rows/buttons.

        Returns:
            int: Number of selected rows.
        """
        return len(self.selected_buttons)

    def update_data(self, new_items):
        self.original_items = new_items
        self._filter_elems()
        self._refresh_buttons()

    def _refresh_buttons(self):
        """
        Refresh the buttons in the ListFilterBox.

        This method updates the body of the ListFilterBox with the current
        data in `items`, ensuring that any changes are reflected in the UI.
        """
        # Clear the body and reconstruct it with updated data
        body = self._construct_body(self.items)
        self.list_walker = urwid.SimpleFocusListWalker(body)
        self.list_box.body = self.list_walker

        if self.items:
            # Put focus in first selectable button
            for idx, widget in enumerate(self.list_walker):
                if widget.selectable():
                    self.list_box.set_focus(idx)
                    break

    def _construct_body(self, items):
        """
        Construct the body of the ListFilterBox.

        This method creates a table structure with headers and rows based on the provided
        list of dictionaries. Each dictionary represents a row, and its keys determine
        the column names.

        Args:
            items (list): A list of dictionaries, where each dictionary represents a row
                             of data in the table.

        Returns:
            list: A list of urwid widgets representing the table header and rows.
        """
        for dict_ in items:
            for key, value in dict_.items():
                value_str = str(value)
                self.columns_size[key] = max(
                    len(value_str), self.columns_size.get(key, len(key) + 1)
                )

        # Building table header with column titles
        columns_str = " | ".join(
            f"{key.ljust(self.columns_size[key])}" for key in self.columns_size.keys()
        )
        divider = "-+-".join(
            "-" * self.columns_size[key] for key in self.columns_size.keys()
        )
        divider = f"+-{divider}+"
        columns_str = f"| {columns_str}|"
        body = [urwid.Text(columns_str), urwid.Text(divider)]
        # Creating rows for each dictionary entry
        for elem in items:
            row = [
                str(elem.get(col, "")).ljust(self.columns_size[col])
                for col in self.columns_size
            ]
            row_button = urwid.Button(" | ".join(row) + "|")
            body.append(urwid.AttrMap(row_button, None, focus_map="reversed"))

        return body

    def create_pop_up(self):
        pop_up_type = self._pop_up_params["pop_up_type"]
        if pop_up_type == self.HELP_POPUP:
            pop_up = PopUpDialog(self._help_message(), title="Help")
            urwid.connect_signal(pop_up, "close", lambda button: self.close_pop_up())
        elif pop_up_type == self.MESSAGE_POPUP:
            pop_up = PopUpDialog(self._pop_up_params["message"])
            urwid.connect_signal(pop_up, "close", lambda button: self.close_pop_up())
        elif pop_up_type == self.FILTER_POPUP:
            # Get column names from the data
            columns = list(self.columns_size.keys()) if self.columns_size else []
            pop_up = FilterPopup(columns, self.current_filters)
            urwid.connect_signal(pop_up, "apply", self._on_filter_apply)
            urwid.connect_signal(pop_up, "cancel", lambda button: self.close_pop_up())
        elif pop_up_type == self.CONFIRMATION_POPUP:
            message = self._pop_up_params.get("message", "Do you confirm?")
            pop_up = ConfirmationPopup(message=message)
            urwid.connect_signal(pop_up, "confirm", self._on_confirmation_confirm)
            urwid.connect_signal(pop_up, "cancel", self._on_confirmation_cancel)
        else:
            raise NotImplementedError(f"Popup type {pop_up_type} does not exist.")
        return pop_up

    def _on_filter_apply(self, popup, filters):
        """
        Handle the application of filters from the filter popup.

        Args:
            popup: The FilterPopup instance that emitted the signal
            filters (dict): Dictionary of column names to regex patterns
        """
        self.current_filters = filters
        self.close_pop_up()

        self._filter_elems()

    def _filter_elems(self):
        # Apply filters to the original data
        if not self.current_filters:
            # No filters, show all data
            self.items = self.original_items[:]
        else:
            # Filter the data based on regex patterns
            filtered_items = []
            for item in self.original_items:
                match_all = True
                for column, pattern in self.current_filters.items():
                    if column in item:
                        try:
                            # Convert item value to string and apply regex
                            item_value = str(item[column])
                            if not re.search(pattern, item_value, re.IGNORECASE):
                                match_all = False
                                break
                        except re.error:
                            # Invalid regex pattern, skip this filter
                            continue
                    else:
                        # Column doesn't exist in item, doesn't match
                        match_all = False
                        break

                if match_all:
                    filtered_items.append(item)

            self.items = filtered_items

        # Clear selections as they might not be valid anymore
        self.selected_buttons.clear()

        # Refresh the display
        self._refresh_buttons()

    def _on_confirmation_confirm(self, popup):
        """
        Handle confirmation of the pending action.

        This method is called when the user confirms the action in the ConfirmationPopup.
        It executes the pending action with the pending items and then closes the popup.

        Args:
            popup: The ConfirmationPopup instance that emitted the signal
        """
        self.close_pop_up()
        log(self, "Action confirmed")

        # Execute the pending action if it exists
        if self.pending_action and self.pending_items is not None:
            self.pending_action(self.pending_items)

        # Clear pending action and items
        self.pending_action = None
        self.pending_items = None

    def _on_confirmation_cancel(self, popup):
        """
        Handle cancellation of the pending action.

        This method is called when the user cancels the action in the ConfirmationPopup.
        It simply closes the popup without executing the pending action.

        Args:
            popup: The ConfirmationPopup instance that emitted the signal
        """
        self.close_pop_up()
        log(self, "Action cancelled")

        # Clear pending action and items without executing
        self.pending_action = None
        self.pending_items = None

    def _help_message(self, sep="\n"):
        message = ""
        for key in self.handlers:
            description = self.handlers[key]["description"]
            message += f"{key}: {description}{sep}"
        message += f"f: filter columns{sep}"
        message += f"arrows/hjkl: move{sep}"
        message += f"space/enter: select{sep}"
        message += f"q: quit{sep}"
        message += "?: help"
        return message

    def get_pop_up_parameters(self):
        terminal_width, terminal_height = os.get_terminal_size()
        if self._pop_up_params["pop_up_type"] == self.FILTER_POPUP:
            overlay_height = len(self.handlers) + 10
            overlay_width = 64
        else:
            overlay_height = len(self.handlers) + 8
            overlay_width = 32

        left = (terminal_width - overlay_width) // 2
        top = (terminal_height - overlay_height) // 2

        return {
            "left": left,
            "top": top,
            "overlay_width": overlay_width,
            "overlay_height": overlay_height,
        }

    def keypress(self, size, key):
        """
        Process user key inputs.

        Args:
        size (tuple): The available screen size for rendering.
        key (str): The key pressed by the user.

        This method handles keypress events, allowing for selection of rows or passing
        unhandled keypresses to the parent class. It also supports navigation using vi keys.
        """
        if key in ("j", "down"):
            return super().keypress(size, "down")
        elif key in ("k", "up"):
            return super().keypress(size, "up")
        elif key in ("h", "left"):
            return super().keypress(size, "left")
        elif key in ("l", "right"):
            return super().keypress(size, "right")
        elif key == "?":
            self.open_pop_up(pop_up_type=self.HELP_POPUP)
        elif key == "f" or key == "/":
            self.open_pop_up(pop_up_type=self.FILTER_POPUP)
        elif key == " " or key == "enter":
            focus_widget, focus_position = self.list_walker.get_focus()
            current_data = self.items[
                focus_position - 2
            ]  # Adjust for header and divider
            self.toggle_selection(focus_widget.original_widget, current_data)
        elif key in ("a", "A"):
            # Select all lines
            self.select_all()
        elif key in ("u", "U"):
            # Unselect all lines
            self.unselect_all()
        elif key.lower() in self.handlers:
            items_selected = list(self.selected_buttons.values())
            if not items_selected and len(self.items) > 0:
                # get current focus
                focus_widget, focus_position = self.list_walker.get_focus()
                if focus_position >= 2:
                    items_selected = [self.items[focus_position - 2]]

            handler = self.handlers[key.lower()]

            # Check if confirmation is required
            if handler.get("confirmation", False):
                # Store the pending action and items
                self.pending_action = handler["callback"]
                self.pending_items = items_selected
                # Show confirmation popup
                self.open_pop_up(
                    pop_up_type=self.CONFIRMATION_POPUP,
                    message=f"Are you sure you want to {handler['description'].lower()}?",
                )
            else:
                # Execute directly without confirmation
                handler["callback"](items_selected)
        else:
            return super().keypress(size, key)

    def select_all(self):
        """
        Select all rows in the ListFilterBox.
        """
        for idx, widget in enumerate(self.list_walker[2:], start=0):
            if isinstance(widget, urwid.AttrMap):
                button = widget.original_widget
                row_data = self.items[idx]
                row_key = self.get_row_key(row_data)
                if row_key not in self.selected_buttons:
                    self._select_button(True, button, row_data)

    def unselect_all(self):
        """
        Unselect all rows in the ListFilterBox.
        """
        for idx, widget in enumerate(self.list_walker[2:], start=0):
            if isinstance(widget, urwid.AttrMap):
                button = widget.original_widget
                row_data = self.items[idx]
                row_key = self.get_row_key(row_data)
                if row_key in self.selected_buttons:
                    self._select_button(False, button, row_data)

    def add_handler(self, key, description, callback, confirmation=False):
        """
        Add a handler for a specific key input.

        Args:
            key (str): The key associated with the action.
            description (str): A description of the action performed by the handler.
            callback (callable): The function to be executed when the key is pressed.
            confirmation (bool): Ask the user to confirm the action before execution.

        This method maps a key to its corresponding action and description, allowing
        for interactive functionality within the ListFilterBox.
        """
        self.handlers[key] = {
            "callback": callback,
            "description": description,
            "confirmation": confirmation,
        }
        self.footer.set_text(self._help_message(sep=" "))

    def toggle_selection(self, button, row_data):
        """
        Toggle the selection state of a given row in the ListFilterBox.

        Args:
            button (urwid.Button): The button widget corresponding to the row.
            row_data (dict): The data dictionary associated with the row.

        This method toggles the selection state of a row, visually updating the button's
        appearance and internally tracking the selected rows.
        """
        row_key = self.get_row_key(row_data)
        self._select_button(row_key not in self.selected_buttons, button, row_data)

    def _select_button(self, select, button, row_data):
        """
        Select or unselect a button representing a row and update its visual state.

        Args:
            select (bool): Whether to select or unselect the button.
            button (urwid.Button): The button widget.
            row_data (dict): The data dictionary associated with the row.
        """
        row_key = self.get_row_key(row_data)
        if select:
            self.selected_buttons[row_key] = row_data
            button.set_label(f"* {button.get_label()} *")  # Highlight selected button
        else:
            self.selected_buttons.pop(row_key)
            button.set_label(
                button.get_label().strip("*").strip()
            )  # Reset button appearance

    def get_row_key(self, row):
        """
        Retrieve a unique key for a given row of data.

        This method uses the `column_key` attribute to obtain a unique identifier for
        a row. If `column_key` is not defined, it defaults to using a tuple of the
        row's items.

        Args:
            row (dict): A dictionary representing a row of data.

        Returns:
            The unique key for the row, either by `column_key` or as a tuple of items.
        """
        if self.column_key is None:
            return tuple(row.items())

        return row[self.column_key]


def main():
    """
    Entry point for the UI application.

    This function initializes the ListFilterBox with sample data and sets up key handlers.
    It also starts the urwid MainLoop to render the UI and handle user interactions.
    """

    def unhandled(key):
        if key in ("q", "Q"):
            raise urwid.ExitMainLoop()

    list_filter = ListFilterBox(
        [
            {"nome": "Mateus", "idade": 35, "profissão": "Engenheiro"},
            {"nome": "Érika", "profissão": "Médica"},
        ],
        title="Profissionais",
    )

    main_loop = urwid.MainLoop(
        urwid.AttrMap(list_filter, "background"),
        palette=NORD_PALETTE,
        unhandled_input=unhandled,
        pop_ups=True,
    )

    def export(students):
        with open("students.txt", "w") as o:
            for student in students:
                o.write(f"{student}\n")
        list_filter.open_pop_up(
            pop_up_type=ListFilterBox.MESSAGE_POPUP,
            message="Students written on students.txt file",
        )

    list_filter.add_handler("w", "Export students to file", export)
    list_filter.add_handler("s", "Show Details", lambda x: print(x))

    list_filter.main_loop = main_loop

    main_loop.run()


if __name__ == "__main__":
    main()
