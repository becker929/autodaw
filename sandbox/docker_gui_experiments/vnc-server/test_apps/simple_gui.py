#!/usr/bin/env python3
"""
Simple Tkinter GUI application for testing Docker GUI via VNC.
"""

import tkinter as tk
from tkinter import messagebox
import os

class SimpleGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Docker GUI Test - VNC Server")
        self.root.geometry("450x350")

        # Main frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title label
        title_label = tk.Label(
            main_frame,
            text="Docker VNC GUI Test Application",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Info label
        info_label = tk.Label(
            main_frame,
            text="This GUI application is running inside a Docker container\nwith a virtual framebuffer and VNC server.\n\nConnect via VNC viewer to see this interface.",
            justify=tk.CENTER,
            wraplength=400
        )
        info_label.pack(pady=(0, 20))

        # Display info
        display_var = os.environ.get('DISPLAY', 'Not set')
        display_info = tk.Label(
            main_frame,
            text=f"Virtual Display: {display_var}",
            font=("Courier", 10),
            fg="blue"
        )
        display_info.pack(pady=(0, 10))

        # Button frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10)

        # Test button
        test_button = tk.Button(
            button_frame,
            text="Show VNC Success Message",
            command=self.show_message,
            font=("Arial", 12),
            bg="lightgreen",
            padx=20
        )
        test_button.pack(side=tk.LEFT, padx=(0, 10))

        # Launch other apps button
        launch_button = tk.Button(
            button_frame,
            text="Launch xeyes",
            command=self.launch_xeyes,
            font=("Arial", 12),
            bg="lightyellow",
            padx=20
        )
        launch_button.pack(side=tk.LEFT, padx=(0, 10))

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

        # Instructions
        instructions = tk.Label(
            main_frame,
            text="Instructions:\n• Connect VNC viewer to localhost:5900\n• No password required for this demo\n• Try launching other applications from terminal",
            justify=tk.LEFT,
            font=("Arial", 10),
            fg="gray",
            wraplength=400
        )
        instructions.pack(side=tk.BOTTOM, pady=(20, 0))

    def show_message(self):
        messagebox.showinfo(
            "VNC Success!",
            "Docker VNC container is working correctly!\n\nVirtual framebuffer + VNC server is functional.\n\nYou can run multiple GUI applications simultaneously."
        )

    def launch_xeyes(self):
        os.system("xeyes &")
        messagebox.showinfo("Launched", "xeyes application started in background")

    def quit_app(self):
        self.root.quit()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SimpleGUI()
    app.run()
