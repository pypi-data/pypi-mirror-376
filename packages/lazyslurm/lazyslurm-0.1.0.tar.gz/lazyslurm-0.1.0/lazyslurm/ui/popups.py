import urwid
from .tab_widgets import TabColumns, TabPile


class PopUpDialog(urwid.WidgetWrap):
    signals = ["close"]

    def __init__(self, text="", title=None):
        close_button = urwid.Button("Press Any Key to close.")
        urwid.connect_signal(
            close_button, "click", lambda button: urwid.emit_signal(self, "close", self)
        )

        pile = urwid.Pile([urwid.Text(text), close_button])
        linebox = urwid.LineBox(pile, title=title)
        super().__init__(urwid.AttrMap(urwid.Filler(linebox), "popup"))


class ConfirmationPopup(urwid.WidgetWrap):
    signals = ["confirm", "cancel"]

    def __init__(
        self,
        message,
        title=None,
        confirm_text="Yes",
        cancel_text="No",
        default="confirm",
    ):
        """
        Initialize the ConfirmationPopup with a message and customizable buttons.

        Args:
            message (str): The question or message to display
            title (str): Optional title for the popup
            confirm_text (str): Text for the confirmation button (default: "Yes")
            cancel_text (str): Text for the cancel button (default: "No")
            default (str): Which button to highlight by default ("confirm" or "cancel")
        """
        self.default = default

        # Create the message text
        message_widget = urwid.Text(message, align="center")

        # Create buttons
        self.confirm_button = urwid.Button(confirm_text, align="center")
        self.cancel_button = urwid.Button(cancel_text, align="center")

        # Connect button signals
        urwid.connect_signal(self.confirm_button, "click", self._on_confirm)
        urwid.connect_signal(self.cancel_button, "click", self._on_cancel)

        # Apply button styling based on default
        if default == "confirm":
            confirm_attr = "button_selected"
            cancel_attr = "button"
        else:
            confirm_attr = "button"
            cancel_attr = "button_selected"

        # Create button row
        button_row = TabColumns(
            [
                ("weight", 1, urwid.AttrMap(self.confirm_button, confirm_attr)),
                ("weight", 1, urwid.AttrMap(self.cancel_button, cancel_attr)),
            ]
        )

        # Create the main layout
        pile_contents = [
            message_widget,
            urwid.Divider(),
            button_row,
        ]

        pile = TabPile(pile_contents)
        linebox = urwid.LineBox(pile, title=title or "Confirmation")

        super().__init__(urwid.AttrMap(urwid.Filler(linebox), "popup"))

    def _on_confirm(self, button):
        """Handle confirm button click"""
        urwid.emit_signal(self, "confirm", self)

    def _on_cancel(self, button):
        """Handle cancel button click"""
        urwid.emit_signal(self, "cancel", self)

    def keypress(self, size, key):
        """Handle key presses in the confirmation popup"""
        key = key.lower()

        if key == "esc":
            # Escape always cancels
            self._on_cancel(None)
            return None
        elif key in ("y", "yes"):
            # Y key confirms
            self._on_confirm(None)
            return None
        elif key in ("n", "no"):
            # N key cancels
            self._on_cancel(None)
            return None
        else:
            return super().keypress(size, key)


class FilterPopup(urwid.WidgetWrap):
    signals = ["apply", "cancel"]

    def __init__(self, columns, current_filters=None):
        """
        Initialize the FilterPopup with column names and optional current filters.

        Args:
            columns (list): List of column names to create filter inputs for
            current_filters (dict): Optional dictionary of current filter values
        """
        self.columns = columns
        self.filter_inputs = {}
        current_filters = current_filters or {}

        # Create input fields for each column
        filter_widgets = []
        filter_widgets.append(
            urwid.Text("Enter regex patterns for filtering (leave empty to ignore):")
        )
        filter_widgets.append(urwid.Divider())

        max_size = max([len(c) for c in columns])

        for column in columns:
            # Create label and input field for each column
            current_value = current_filters.get(column, "")
            input_field = urwid.Edit(f"{column:{max_size}}: ", current_value)
            self.filter_inputs[column] = input_field
            filter_widgets.append(input_field)

        filter_widgets.append(urwid.Divider())

        # Create buttons
        self.apply_button = urwid.Button("Apply Filters", align="center")
        self.cancel_button = urwid.Button("Cancel", align="center")
        self.clear_button = urwid.Button("Clear All", align="center")

        urwid.connect_signal(self.apply_button, "click", self._on_apply)
        urwid.connect_signal(self.cancel_button, "click", self._on_cancel)
        urwid.connect_signal(self.clear_button, "click", self._on_clear)

        self.button_row = TabColumns(
            [
                ("weight", 1, urwid.AttrMap(self.apply_button, "button")),
                ("weight", 1, urwid.AttrMap(self.cancel_button, "button")),
                ("weight", 1, urwid.AttrMap(self.clear_button, "button")),
            ]
        )

        filter_widgets.append(self.button_row)

        # Create the main pile widget
        self.pile = TabPile(filter_widgets)
        linebox = urwid.LineBox(self.pile, title="Filter Columns")

        super().__init__(urwid.AttrMap(urwid.Filler(linebox), "popup"))

    def _on_apply(self, button):
        """Handle apply button click"""
        filters = {}
        for column, input_field in self.filter_inputs.items():
            filter_text = input_field.get_edit_text().strip()
            if filter_text:
                filters[column] = filter_text
        urwid.emit_signal(self, "apply", self, filters)

    def _on_cancel(self, button):
        """Handle cancel button click"""
        urwid.emit_signal(self, "cancel", self)

    def _on_clear(self, button):
        """Handle clear button click"""
        for input_field in self.filter_inputs.values():
            input_field.set_edit_text("")

    def keypress(self, size, key):
        """Handle key presses in the filter popup"""
        if key == "enter" and self.pile.focus != self.button_row:
            # Apply filters when Enter is pressed and not focusing a button
            self._on_apply(None)
            return None
        elif key == "esc":
            # Cancel when Escape is pressed
            self._on_cancel(None)
            return None
        else:
            return super().keypress(size, key)
