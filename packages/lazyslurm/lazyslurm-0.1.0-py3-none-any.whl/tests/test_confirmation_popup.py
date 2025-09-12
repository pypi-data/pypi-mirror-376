#!/usr/bin/env python3
"""
Test script for the ConfirmationPopup widget
"""

import urwid
from lazyslurm.ui.popups import ConfirmationPopup


class TestApp:
    def __init__(self):
        self.loop = None
        self.main_widget = None
        self.popup_open = False
        
    def show_confirmation(self, message, title=None, confirm_text="Yes", cancel_text="No", default="confirm"):
        """Show a confirmation popup"""
        if self.popup_open:
            return
            
        popup = ConfirmationPopup(
            message=message,
            title=title,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            default=default
        )
        
        # Connect signals
        urwid.connect_signal(popup, 'confirm', self.on_confirm)
        urwid.connect_signal(popup, 'cancel', self.on_cancel)
        
        # Show popup as overlay
        overlay = urwid.Overlay(
            popup,
            self.main_widget,
            align='center',
            width=50,
            valign='middle',
            height=10
        )
        
        self.loop.widget = overlay
        self.popup_open = True
        
    def on_confirm(self, popup):
        """Handle confirmation"""
        self.close_popup()
        self.show_result("You clicked YES!")
        
    def on_cancel(self, popup):
        """Handle cancellation"""
        self.close_popup()
        self.show_result("You clicked NO!")
        
    def close_popup(self):
        """Close the popup and return to main widget"""
        self.loop.widget = self.main_widget
        self.popup_open = False
        
    def show_result(self, message):
        """Show result message"""
        result_text = urwid.Text(f"\n{message}\n\nPress 'q' to quit, 's' to show popup again")
        result_widget = urwid.Filler(urwid.Padding(result_text, align='center'))
        self.loop.widget = result_widget
        
    def unhandled_input(self, key):
        """Handle global key presses"""
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif key in ('s', 'S'):
            self.show_confirmation(
                message="Are you sure you want to continue?",
                title="Confirmation Required",
                confirm_text="Continue",
                cancel_text="Cancel",
                default="confirm"
            )
        elif key in ('d', 'D'):
            # Test with different default
            self.show_confirmation(
                message="Do you want to delete this file?",
                title="Delete File",
                confirm_text="Delete",
                cancel_text="Keep",
                default="cancel"
            )
            
    def run(self):
        """Run the test application"""
        # Create main widget
        instructions = urwid.Text([
            "Confirmation Popup Test\n\n",
            "Press 's' to show confirmation popup (default: Yes)\n",
            "Press 'd' to show deletion popup (default: No)\n",
            "Press 'q' to quit\n\n",
            "In popup:\n",
            "- Enter: Select default option\n",
            "- Esc: Cancel\n",
            "- Y/Yes: Confirm\n",
            "- N/No: Cancel\n",
            "- Tab: Switch between buttons"
        ])
        
        self.main_widget = urwid.Filler(urwid.Padding(instructions, align='center'))
        
        # Create color palette
        palette = [
            ('popup', 'white', 'dark blue'),
            ('button', 'white', 'dark blue'),
            ('button_selected', 'yellow', 'dark red'),
        ]
        
        # Start main loop
        self.loop = urwid.MainLoop(
            self.main_widget,
            palette=palette,
            unhandled_input=self.unhandled_input
        )
        
        self.loop.run()


if __name__ == '__main__':
    app = TestApp()
    app.run()
