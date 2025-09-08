#!/usr/bin/env python3
"""
Simple Tkinter GUI application for testing Docker GUI forwarding.
"""

import tkinter as tk
from tkinter import messagebox
import sys

class SimpleGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Docker GUI Test - X11 Forwarding")
        self.root.geometry("400x300")

        # Main frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title label
        title_label = tk.Label(
            main_frame,
            text="Docker GUI Test Application",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Info label
        info_label = tk.Label(
            main_frame,
            text="This GUI application is running inside a Docker container\nusing X11 forwarding to display on macOS.",
            justify=tk.CENTER,
            wraplength=350
        )
        info_label.pack(pady=(0, 20))

        # Button frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10)

        # Test button
        test_button = tk.Button(
            button_frame,
            text="Show Message",
            command=self.show_message,
            font=("Arial", 12),
            bg="lightblue",
            padx=20
        )
        test_button.pack(side=tk.LEFT, padx=(0, 10))

        # Quit button
        quit_button = tk.Button(
            button_frame,
            text="Quit",
            command=self.quit_app,
            font=("Arial", 12),
            bg="lightcoral",
            padx=20
        )
        quit_button.pack(side=tk.LEFT)

        # Display info
        display_info = tk.Label(
            main_frame,
            text=f"DISPLAY: {sys.platform} - X11 forwarding active",
            font=("Courier", 10),
            fg="gray"
        )
        display_info.pack(side=tk.BOTTOM, pady=(20, 0))

    def show_message(self):
        messagebox.showinfo(
            "Success!",
            "Docker GUI container is working correctly!\n\nX11 forwarding is functional."
        )

    def quit_app(self):
        self.root.quit()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SimpleGUI()
    app.run()
