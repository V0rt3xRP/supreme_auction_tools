import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
import csv
import os
import shutil
import subprocess
import time
from PIL import Image, ImageTk, ImageDraw, ImageFont
import pandas as pd
import random
import requests
import json
import sys
import tempfile
import zipfile
from packaging import version
import winreg  # For Windows registry access
import webbrowser

# Current version of the application
APP_VERSION = "1.1.0"
APP_NAME = "ReNinja"
GITHUB_REPO = "V0rt3xRP/supreme_auction_tools"  # Updated repository
UPDATE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
TEMP_UPDATE_DIR = os.path.join(tempfile.gettempdir(), "reninja_update")

class UpdateChecker:
    CURRENT_VERSION = "1.1.0"  # Update this when you release new versions
    GITHUB_API_URL = "https://api.github.com/repos/V0rt3xRP/supreme_auction_tools/releases/latest"

    @staticmethod
    def check_for_updates():
        try:
            response = requests.get(UpdateChecker.GITHUB_API_URL)
            if response.status_code == 200:
                latest_release = response.json()
                latest_version = latest_release['tag_name'].replace('v', '')
                
                if version.parse(latest_version) > version.parse(UpdateChecker.CURRENT_VERSION):
                    return True, latest_version, latest_release['html_url']
            return False, None, None
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return False, None, None

class UpdateNotification(ctk.CTkToplevel):
    def __init__(self, parent, latest_version, download_url):
        super().__init__(parent)
        
        self.title("Update Available")
        self.geometry("400x150")
        
        # Center the window
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        # Make window float on top
        self.attributes('-topmost', True)
        
        # Add widgets
        ctk.CTkLabel(self, 
                    text=f"A new version (v{latest_version}) is available!",
                    font=("Arial", 14, "bold")).pack(pady=10)
        
        ctk.CTkLabel(self, 
                    text="Would you like to download the update?",
                    font=("Arial", 12)).pack(pady=5)
        
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=10)
        
        ctk.CTkButton(button_frame, 
                     text="Download", 
                     command=lambda: self.open_download(download_url)).pack(side="left", padx=10)
        
        ctk.CTkButton(button_frame, 
                     text="Later", 
                     command=self.destroy).pack(side="left", padx=10)

    def open_download(self, url):
        webbrowser.open(url)
        self.destroy()

class ImageRenamerApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Retool - The Supreme Image Renamer")
        self.app.geometry("1200x800")
        self.app.resizable(True, True)  # Allow both horizontal and vertical resizing
        self.app.minsize(800, 600)  # Set minimum window size to prevent too small windows

        # Initialize update checker
        self.update_checker = UpdateChecker()
        
        # Check for updates after a short delay
        self.app.after(2000, self.check_for_updates)

        # Set window icon
        try:
            icon_path = os.path.join("assets", "reninja_logo.png")
            icon_image = Image.open(icon_path)
            # For Windows taskbar icon
            if os.name == 'nt':  # Windows
                icon_ico = os.path.join("assets", "reninja_logo.ico")
                icon_image.save(icon_ico, format='ICO')
                self.app.iconbitmap(icon_ico)
            else:  # For Linux/Mac
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.app.iconphoto(True, icon_photo)
        except Exception as e:
            print(f"Could not load application icon: {e}")

        # Force dark mode
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Custom colors (only dark theme colors now)
        self.colors = {
            "bg": "#1c1c1e",
            "fg": "#ffffff",
            "accent": "#0A84FF",
            "success": "#30D158",
            "button": "#0A84FF",
            "button_hover": "#0051FF",
            "progress": "#0A84FF",
            "border": "#3a3a3c"
        }

        # Variables
        self.old_lot_column = ctk.StringVar(value="Select column")
        self.new_lot_column = ctk.StringVar(value="Select column")
        self.csv_data = []
        self.folder_path = ""
        self.output_folder = ""
        self.history = []
        self.undo_stack = []

        # Create main layout
        self.create_layout()

    def create_layout(self):
        # Create main container
        self.main_container = ctk.CTkFrame(
            self.app,
            corner_radius=15,
            fg_color=("gray95", "gray10"),
            border_width=1,
            border_color=self.colors["border"]
        )
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Create header with settings
        self.create_header()
        
        # Create two-column layout for the main interface
        self.tools_sidebar = ctk.CTkFrame(
            self.main_container,
            width=200,
            corner_radius=0,
            fg_color=("gray90", "gray15")
        )
        self.tools_sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.tools_sidebar.pack_propagate(False)

        # Create tools list in sidebar
        self.create_tools_sidebar()

        # Create main content area for tools
        self.content_area = ctk.CTkFrame(
            self.main_container,
            corner_radius=0,
            fg_color=("gray90", "gray15")
        )
        self.content_area.pack(side="left", fill="both", expand=True, padx=2, pady=0)

        # Show welcome screen initially
        self.show_welcome_screen()

    def create_tools_sidebar(self):
        # Title for tools list
        title = ctk.CTkLabel(
            self.tools_sidebar,
            text="Available Tools",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        )
        title.pack(pady=20)

        # Create buttons for each tool
        tools = [
            ("ReNinja", self.show_reninja_tool, "CSV-based image renaming tool"),
            ("ReMystery", self.show_mystory_tool, "Sequential batch image renaming"),
            ("ReMark", self.show_remark_tool, "Add watermark to catalog images")
        ]

        for tool_name, command, description in tools:
            tool_frame = ctk.CTkFrame(
                self.tools_sidebar,
                fg_color="transparent"
            )
            tool_frame.pack(fill="x", padx=10, pady=5)

            tool_button = ctk.CTkButton(
                tool_frame,
                text=tool_name,
                command=command,
                height=40,
                corner_radius=8,
                font=ctk.CTkFont(size=14),
                fg_color=self.colors["button"],
                hover_color=self.colors["button_hover"]
            )
            tool_button.pack(fill="x")

            # Tool description
            desc_label = ctk.CTkLabel(
                tool_frame,
                text=description,
                font=ctk.CTkFont(size=11),
                text_color="gray70",
                wraplength=180
            )
            desc_label.pack(pady=(2, 0))

    def show_welcome_screen(self):
        # Clear content area
        for widget in self.content_area.winfo_children():
            widget.destroy()

        # Create welcome content
        welcome_frame = ctk.CTkFrame(
            self.content_area,
            fg_color="transparent"
        )
        welcome_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Welcome message
        ctk.CTkLabel(
            welcome_frame,
            text="Welcome to ReTools",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["accent"]
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            welcome_frame,
            text="Select a tool from the sidebar to get started",
            font=ctk.CTkFont(size=14)
        ).pack()

    def show_reninja_tool(self):
        # Clear content area
        for widget in self.content_area.winfo_children():
            widget.destroy()

        # Create ReNinja interface in content area
        reninja_frame = ctk.CTkFrame(
            self.content_area,
            fg_color="transparent"
        )
        reninja_frame.pack(fill="both", expand=True)

        # Create the original ReNinja layout within this frame
        self.create_reninja_tab(reninja_frame)

    def show_mystory_tool(self):
        # Clear content area
        for widget in self.content_area.winfo_children():
            widget.destroy()

        # Create ReMystery interface in content area
        mystory_frame = ctk.CTkFrame(
            self.content_area,
            fg_color="transparent"
        )
        mystory_frame.pack(fill="both", expand=True)

        # Create the ReMystery layout within this frame
        self.create_mystory_tab(mystory_frame)

    def show_remark_tool(self):
        # Clear content area
        for widget in self.content_area.winfo_children():
            widget.destroy()

        # Create ReMark interface in content area
        remark_frame = ctk.CTkFrame(
            self.content_area,
            fg_color="transparent"
        )
        remark_frame.pack(fill="both", expand=True)

        # Create the ReMark layout within this frame
        self.create_remark_tab(remark_frame)

    def create_reninja_tab(self, parent):
        # Create two-column layout
        self.create_sidebar(parent)
        self.create_main_area(parent)

    def create_mystory_tab(self, parent):
        # Create two-column layout
        self.create_mystory_sidebar(parent)
        self.create_mystory_main_area(parent)

    def create_mystory_sidebar(self, parent):
        # Sidebar container
        mystory_sidebar = ctk.CTkFrame(
            parent,
            width=300,
            corner_radius=0,
            fg_color=("gray90", "gray15")
        )
        mystory_sidebar.pack(side="left", fill="y", padx=0, pady=0)
        mystory_sidebar.pack_propagate(False)

        # Input folder section with status
        input_frame = ctk.CTkFrame(mystory_sidebar, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=10)
        
        input_label = ctk.CTkLabel(
            input_frame,
            text="Input Folder",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        input_label.pack(anchor="w")
        
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(5, 0))
        
        self.mystory_input_button = ctk.CTkButton(
            button_frame,
            text="Select Input Folder",
            command=self.select_mystory_input,
            height=32,
            corner_radius=8
        )
        self.mystory_input_button.pack(side="left", fill="x", expand=True)
        
        self.mystory_input_status = ctk.CTkLabel(
            button_frame,
            text="❌",
            font=ctk.CTkFont(size=16),
            width=30
        )
        self.mystory_input_status.pack(side="right", padx=(10, 0))

        # Output folder section with status
        output_frame = ctk.CTkFrame(mystory_sidebar, fg_color="transparent")
        output_frame.pack(fill="x", padx=20, pady=10)
        
        output_label = ctk.CTkLabel(
            output_frame,
            text="Output Folder",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        output_label.pack(anchor="w")
        
        button_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(5, 0))
        
        self.mystory_output_button = ctk.CTkButton(
            button_frame,
            text="Select Output Folder",
            command=self.select_mystory_output,
            height=32,
            corner_radius=8
        )
        self.mystory_output_button.pack(side="left", fill="x", expand=True)
        
        self.mystory_output_status = ctk.CTkLabel(
            button_frame,
            text="❌",
            font=ctk.CTkFont(size=16),
            width=30
        )
        self.mystory_output_status.pack(side="right", padx=(10, 0))

        # Sequence number section
        sequence_frame = ctk.CTkFrame(mystory_sidebar, fg_color="transparent")
        sequence_frame.pack(fill="x", padx=20, pady=10)
        
        sequence_label = ctk.CTkLabel(
            sequence_frame,
            text="Starting Sequence Number:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        sequence_label.pack(anchor="w")
        
        self.current_sequence = ctk.StringVar(value="1")
        sequence_entry = ctk.CTkEntry(
            sequence_frame,
            textvariable=self.current_sequence,
            width=260,
            height=32
        )
        sequence_entry.pack(pady=(5, 0))

        # Create status frame for bottom elements
        status_frame = ctk.CTkFrame(mystory_sidebar, fg_color="transparent")
        status_frame.pack(side="bottom", fill="x", padx=20, pady=20)

        # Process button
        self.mystory_action_button = ctk.CTkButton(
            status_frame,
            text="Process Batch",
            command=self.process_mystory_batch,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["success"]
        )
        self.mystory_action_button.pack(pady=(0, 20))

        # Progress bar
        self.mystory_progress = ctk.CTkProgressBar(
            status_frame,
            height=6,
            corner_radius=3,
            progress_color=self.colors["accent"]
        )
        self.mystory_progress.pack(fill="x", pady=(0, 10))
        self.mystory_progress.set(0)

        # Status label
        self.mystory_status = ctk.CTkLabel(
            status_frame,
            text="Status: Ready",
            font=ctk.CTkFont(size=12)
        )
        self.mystory_status.pack(anchor="w")

    def create_mystory_main_area(self, parent):
        # Main content area
        mystory_main = ctk.CTkFrame(
            parent,
            corner_radius=0,
            fg_color="transparent"
        )
        mystory_main.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        # Welcome section
        welcome_frame = ctk.CTkFrame(
            mystory_main,
            fg_color=("gray85", "gray17"),
            corner_radius=10
        )
        welcome_frame.pack(fill="x", pady=(0, 20))

        # Welcome header
        ctk.CTkLabel(
            welcome_frame,
            text="Welcome to ReMystery",
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"),
            text_color=self.colors["accent"]
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            welcome_frame,
            text="Sequential Batch Image Renaming Tool",
            font=ctk.CTkFont(size=14)
        ).pack(pady=(0, 20))

        # Quick start guide
        guide_frame = ctk.CTkFrame(
            mystory_main,
            fg_color=("gray85", "gray17"),
            corner_radius=10
        )
        guide_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            guide_frame,
            text="Quick Start Guide",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        ).pack(pady=(20, 10))

        steps = [
            ("1. Select Input", "Choose the folder containing your images"),
            ("2. Select Output", "Choose where to save the renamed images"),
            ("3. Set Sequence", "Enter the starting sequence number"),
            ("4. Process", "Click 'Process Batch' to rename all images")
        ]

        for step, desc in steps:
            step_frame = ctk.CTkFrame(guide_frame, fg_color="transparent")
            step_frame.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(
                step_frame,
                text=step,
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left")
            
            ctk.CTkLabel(
                step_frame,
                text=desc,
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=(10, 0))

    def create_remark_tab(self, parent):
        # Create two-column layout
        self.create_remark_sidebar(parent)
        self.create_remark_main_area(parent)

    def create_remark_sidebar(self, parent):
        # Sidebar container
        remark_sidebar = ctk.CTkFrame(
            parent,
            width=300,
            corner_radius=0,
            fg_color=("gray90", "gray15")
        )
        remark_sidebar.pack(side="left", fill="y", padx=0, pady=0)
        remark_sidebar.pack_propagate(False)

        # Input folder section with status
        input_frame = ctk.CTkFrame(remark_sidebar, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=10)
        
        input_label = ctk.CTkLabel(
            input_frame,
            text="Input Folder",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        input_label.pack(anchor="w")
        
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(5, 0))
        
        self.remark_input_button = ctk.CTkButton(
            button_frame,
            text="Select Input Folder",
            command=self.select_remark_input,
            height=32,
            corner_radius=8
        )
        self.remark_input_button.pack(side="left", fill="x", expand=True)
        
        self.remark_input_status = ctk.CTkLabel(
            button_frame,
            text="❌",
            font=ctk.CTkFont(size=16),
            width=30
        )
        self.remark_input_status.pack(side="right", padx=(10, 0))

        # Output folder section with status
        output_frame = ctk.CTkFrame(remark_sidebar, fg_color="transparent")
        output_frame.pack(fill="x", padx=20, pady=10)
        
        output_label = ctk.CTkLabel(
            output_frame,
            text="Output Folder",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        output_label.pack(anchor="w")
        
        button_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(5, 0))
        
        self.remark_output_button = ctk.CTkButton(
            button_frame,
            text="Select Output Folder",
            command=self.select_remark_output,
            height=32,
            corner_radius=8
        )
        self.remark_output_button.pack(side="left", fill="x", expand=True)
        
        self.remark_output_status = ctk.CTkLabel(
            button_frame,
            text="❌",
            font=ctk.CTkFont(size=16),
            width=30
        )
        self.remark_output_status.pack(side="right", padx=(10, 0))

        # Watermark Settings Section
        settings_frame = ctk.CTkFrame(remark_sidebar, fg_color="transparent")
        settings_frame.pack(fill="x", padx=20, pady=10)
        
        settings_label = ctk.CTkLabel(
            settings_frame,
            text="Watermark Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        settings_label.pack(anchor="w", pady=(0, 10))

        # Watermark Text
        text_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        text_frame.pack(fill="x", pady=5)
        
        text_label = ctk.CTkLabel(text_frame, text="Text:")
        text_label.pack(side="left")
        
        self.watermark_text = ctk.StringVar(value="Supreme Auction Catalog Image")
        text_entry = ctk.CTkEntry(
            text_frame,
            textvariable=self.watermark_text,
            placeholder_text="Enter custom watermark text"
        )
        text_entry.pack(side="left", padx=10, fill="x", expand=True)

        def reset_text():
            self.watermark_text.set("Supreme Auction Catalog Image")
        
        reset_button = ctk.CTkButton(
            text_frame,
            text="↺",
            width=30,
            command=reset_text,
            font=ctk.CTkFont(size=14)
        )
        reset_button.pack(side="right")

        # Text Size
        size_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        size_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(size_frame, text="Size:").pack(side="left")
        
        self.watermark_size = ctk.StringVar(value="3.5")
        size_entry = ctk.CTkEntry(
            size_frame,
            width=50,
            textvariable=self.watermark_size
        )
        size_entry.pack(side="left", padx=10)
        
        ctk.CTkLabel(size_frame, text="% of image").pack(side="left")

        # Text Opacity
        opacity_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        opacity_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(opacity_frame, text="Opacity:").pack(side="left")
        
        self.watermark_opacity = ctk.IntVar(value=90)
        opacity_slider = ctk.CTkSlider(
            opacity_frame,
            from_=0,
            to=100,
            variable=self.watermark_opacity,
            width=160
        )
        opacity_slider.pack(side="left", padx=10)
        
        opacity_value = ctk.CTkLabel(opacity_frame, text="90%")
        opacity_value.pack(side="left")
        
        def update_opacity(value):
            opacity_value.configure(text=f"{int(value)}%")
        
        opacity_slider.configure(command=update_opacity)

        # Background Settings
        bg_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        bg_frame.pack(fill="x", pady=5)
        
        self.bg_enabled = ctk.BooleanVar(value=False)
        bg_switch = ctk.CTkSwitch(
            bg_frame,
            text="Background",
            variable=self.bg_enabled,
            onvalue=True,
            offvalue=False
        )
        bg_switch.pack(side="left")

        # Background Color
        self.bg_color = ctk.StringVar(value="#000000")
        
        def pick_color():
            color = colorchooser.askcolor(title="Choose Background Color")
            if color[1]:
                self.bg_color.set(color[1])
                color_button.configure(fg_color=color[1])

        color_button = ctk.CTkButton(
            bg_frame,
            text="",
            width=30,
            height=20,
            fg_color=self.bg_color.get(),
            command=pick_color
        )
        color_button.pack(side="right", padx=10)

        # Background Opacity
        bg_opacity_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        bg_opacity_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(bg_opacity_frame, text="BG Opacity:").pack(side="left")
        
        self.bg_opacity = ctk.IntVar(value=50)
        bg_opacity_slider = ctk.CTkSlider(
            bg_opacity_frame,
            from_=0,
            to=100,
            variable=self.bg_opacity,
            width=160
        )
        bg_opacity_slider.pack(side="left", padx=10)
        
        bg_opacity_value = ctk.CTkLabel(bg_opacity_frame, text="50%")
        bg_opacity_value.pack(side="left")
        
        def update_bg_opacity(value):
            bg_opacity_value.configure(text=f"{int(value)}%")
        
        bg_opacity_slider.configure(command=update_bg_opacity)

        # Create status frame for bottom elements
        status_frame = ctk.CTkFrame(remark_sidebar, fg_color="transparent")
        status_frame.pack(side="bottom", fill="x", padx=20, pady=20)

        # Process button
        self.remark_action_button = ctk.CTkButton(
            status_frame,
            text="Add Watermarks",
            command=self.process_watermarks,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["success"]
        )
        self.remark_action_button.pack(pady=(0, 20))

        # Progress bar
        self.remark_progress = ctk.CTkProgressBar(
            status_frame,
            height=6,
            corner_radius=3,
            progress_color=self.colors["accent"]
        )
        self.remark_progress.pack(fill="x", pady=(0, 10))
        self.remark_progress.set(0)

        # Status label
        self.remark_status = ctk.CTkLabel(
            status_frame,
            text="Status: Ready",
            font=ctk.CTkFont(size=12)
        )
        self.remark_status.pack(anchor="w")

    def create_remark_main_area(self, parent):
        # Main content area
        remark_main = ctk.CTkFrame(
            parent,
            corner_radius=0,
            fg_color="transparent"
        )
        remark_main.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        # Welcome section
        welcome_frame = ctk.CTkFrame(
            remark_main,
            fg_color=("gray85", "gray17"),
            corner_radius=10
        )
        welcome_frame.pack(fill="x", pady=(0, 20))

        # Welcome header
        ctk.CTkLabel(
            welcome_frame,
            text="Welcome to ReMark",
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"),
            text_color=self.colors["accent"]
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            welcome_frame,
            text="Watermark Your Catalog Images",
            font=ctk.CTkFont(size=14)
        ).pack(pady=(0, 20))

        # Quick start guide
        guide_frame = ctk.CTkFrame(
            remark_main,
            fg_color=("gray85", "gray17"),
            corner_radius=10
        )
        guide_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            guide_frame,
            text="Quick Start Guide",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        ).pack(pady=(20, 10))

        steps = [
            ("1. Select Input", "Choose the folder containing your images"),
            ("2. Select Output", "Choose where to save the watermarked images"),
            ("3. Process", "Click 'Add Watermarks' to process all images")
        ]

        for step, desc in steps:
            step_frame = ctk.CTkFrame(guide_frame, fg_color="transparent")
            step_frame.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(
                step_frame,
                text=step,
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left")
            
            ctk.CTkLabel(
                step_frame,
                text=desc,
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=(10, 0))

    def create_header(self):
        # Header container
        self.header_frame = ctk.CTkFrame(
            self.main_container,
            height=50,  # Keep header height at 50
            corner_radius=0,
            fg_color="gray15"
        )
        self.header_frame.pack(fill="x", padx=0, pady=0)
        self.header_frame.pack_propagate(False)

        # Reset button
        self.reset_button = ctk.CTkButton(
            self.header_frame,
            text="Reset",
            width=80,
            height=32,
            corner_radius=8,
            command=self.reset_app,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["button"],
            hover_color=self.colors["button_hover"]
        )
        self.reset_button.pack(side="right", padx=(0, 10))

    def create_sidebar(self, parent):
        # Sidebar container
        self.sidebar = ctk.CTkFrame(
            parent,
            width=300,
            corner_radius=0,
            fg_color=("gray90", "gray15")
        )
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)

        # CSV Section with status
        csv_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        csv_frame.pack(fill="x", padx=20, pady=10)
        
        csv_label = ctk.CTkLabel(
            csv_frame,
            text="CSV File",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        csv_label.pack(anchor="w")
        
        button_frame = ctk.CTkFrame(csv_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(5, 0))
        
        self.csv_button = ctk.CTkButton(
            button_frame,
            text="Upload CSV",
            command=self.load_csv,
            height=32,
            corner_radius=8
        )
        self.csv_button.pack(side="left", fill="x", expand=True)
        
        self.csv_status = ctk.CTkLabel(
            button_frame,
            text="❌",
            font=ctk.CTkFont(size=16),
            width=30
        )
        self.csv_status.pack(side="right", padx=(10, 0))

        # Column selection
        self.create_columns_section()

        # Image folder section with status
        image_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        image_frame.pack(fill="x", padx=20, pady=10)
        
        image_label = ctk.CTkLabel(
            image_frame,
            text="Image Folder",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        image_label.pack(anchor="w")
        
        button_frame = ctk.CTkFrame(image_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(5, 0))
        
        self.image_button = ctk.CTkButton(
            button_frame,
            text="Select Image Folder",
            command=self.upload_images,
            height=32,
            corner_radius=8
        )
        self.image_button.pack(side="left", fill="x", expand=True)
        
        self.image_status = ctk.CTkLabel(
            button_frame,
            text="❌",
            font=ctk.CTkFont(size=16),
            width=30
        )
        self.image_status.pack(side="right", padx=(10, 0))

        # Output folder section with status
        output_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        output_frame.pack(fill="x", padx=20, pady=10)
        
        output_label = ctk.CTkLabel(
            output_frame,
            text="Output Folder",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        output_label.pack(anchor="w")
        
        button_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(5, 0))
        
        self.output_button = ctk.CTkButton(
            button_frame,
            text="Select Output Folder",
            command=self.select_output_folder,
            height=32,
            corner_radius=8
        )
        self.output_button.pack(side="left", fill="x", expand=True)
        
        self.output_status = ctk.CTkLabel(
            button_frame,
            text="❌",
            font=ctk.CTkFont(size=16),
            width=30
        )
        self.output_status.pack(side="right", padx=(10, 0))

        # Create status frame for bottom elements
        status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        status_frame.pack(side="bottom", fill="x", padx=20, pady=20)

        # Process button - now inside status_frame at the top
        self.action_button = ctk.CTkButton(
            status_frame,
            text="Filter and Rename Images",
            command=self.filter_and_rename_images,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["success"]
        )
        self.action_button.pack(pady=(0, 20))  # Add padding below the button

        # Progress bar
        self.progress = ctk.CTkProgressBar(
            status_frame,
            height=6,
            corner_radius=3,
            progress_color=self.colors["accent"]
        )
        self.progress.pack(fill="x", pady=(0, 10))
        self.progress.set(0)

        # Status label
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Status: Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(anchor="w")

    def create_main_area(self, parent):
        # Main content area
        self.main_area = ctk.CTkFrame(
            parent,
            corner_radius=0,
            fg_color="transparent"
        )
        self.main_area.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        # Create landing page
        self.create_landing_page()

    def create_sidebar_section(self, title, button_text, command):
        frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkButton(
            frame,
            text=button_text,
            command=command,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["button"],
            hover_color=self.colors["button_hover"]
        ).pack(fill="x", pady=(5, 0))

    def update_csv_preview(self):
        # Clear existing content
        for widget in self.header_frame.winfo_children():
            widget.destroy()
        for widget in self.table_container.winfo_children():
            widget.destroy()

        if self.csv_data:
            # Get column headers
            headers = list(self.csv_data[0].keys())
            
            # Create frames for each column
            self.column_frames = []
            
            # Set up headers
            for col, header in enumerate(headers):
                # Create column frame in header
                header_label = ctk.CTkLabel(
                    self.header_frame,
                    text=header,
                    font=ctk.CTkFont(family="Helvetica", size=12, weight="bold"),
                    fg_color=self.colors["accent"],
                    text_color="white",
                    corner_radius=0,
                    width=200,
                    height=40
                )
                header_label.grid(row=0, column=col, padx=1, pady=1, sticky="nsew")
                self.header_frame.grid_columnconfigure(col, weight=1)

                # Create column frame for data
                column_frame = ctk.CTkFrame(
                    self.table_container,
                    fg_color="transparent"
                )
                column_frame.grid(row=0, column=col, sticky="nsew", padx=1)
                self.column_frames.append(column_frame)
                self.table_container.grid_columnconfigure(col, weight=1)

            # Add data rows
            for row_idx, row_data in enumerate(self.csv_data):
                row_color = ("gray17" if row_idx % 2 == 0 else "gray13")
                
                for col_idx, header in enumerate(headers):
                    cell = ctk.CTkLabel(
                        self.column_frames[col_idx],
                        text=str(row_data[header]),
                        font=ctk.CTkFont(family="Helvetica", size=12),
                        fg_color=row_color,
                        corner_radius=0,
                        width=200,
                        height=35,
                        anchor="w",
                        padx=10
                    )
                    cell.pack(fill="x", pady=1)

            # Configure header columns to match data columns
            for col in range(len(headers)):
                self.header_frame.grid_columnconfigure(col, weight=1)

    def update_images_preview(self):
        # Clear existing images
        for widget in self.images_frame.winfo_children():
            widget.destroy()

        if self.folder_path:
            # Initialize storage for loaded images
            self.loaded_images = []
            self.image_widgets = []
            
            # Disable scrolling during loading
            self.images_frame._parent_canvas.configure(state="disabled")
            
            images = [f for f in os.listdir(self.folder_path) 
                     if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            # Sort images numerically
            def natural_sort_key(s):
                import re
                return [int(text) if text.isdigit() else text.lower()
                       for text in re.split(r'([0-9]+)', os.path.splitext(s)[0])]
            
            images.sort(key=natural_sort_key)
            
            # Create centered loading container
            self.loading_container = ctk.CTkFrame(
                self.images_frame,
                fg_color="transparent"
            )
            self.loading_container.pack(expand=True, fill="both")
            
            # Create empty space to center loading bar
            ctk.CTkFrame(self.loading_container, fg_color="transparent", height=200).pack()
            
            # Set up grid parameters
            self.grid_width = 4  # Number of images per row
            total_images = len(images)
            
            def load_image(index):
                if index >= total_images:
                    # All images loaded, now display them
                    self.loading_container.destroy()
                    display_loaded_images()
                    self.images_frame._parent_canvas.configure(state="normal")
                    self.status_label.configure(text="Images loaded successfully")
                    self.progress.set(0)
                    return

                try:
                    # Update progress
                    progress = (index + 1) / total_images
                    self.progress.set(progress)
                    self.status_label.configure(text=f"Loading images... {index + 1}/{total_images}")
                    
                    img_name = images[index]
                    img_path = os.path.join(self.folder_path, img_name)
                    img = Image.open(img_path)
                    
                    # Calculate aspect ratio and resize maintaining it
                    target_width = 200  # Maximum width
                    target_height = 150  # Maximum height
                    
                    # Calculate scaling factors for both dimensions
                    width_ratio = target_width / img.width
                    height_ratio = target_height / img.height
                    
                    # Use the smaller ratio to ensure image fits within bounds
                    scale_factor = min(width_ratio, height_ratio)
                    
                    # Calculate new dimensions
                    new_width = int(img.width * scale_factor)
                    new_height = int(img.height * scale_factor)
                    
                    # Resize image
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    ctk_img = ctk.CTkImage(
                        light_image=img,
                        dark_image=img,
                        size=(new_width, new_height)
                    )
                    
                    # Store image and its data
                    self.loaded_images.append(ctk_img)
                    self.image_widgets.append({
                        'image': ctk_img,
                        'name': img_name,
                        'index': index
                    })
                    
                except Exception as e:
                    print(f"Error loading image {img_name}: {e}")

                # Schedule next image load
                self.app.after(100, load_image, index + 1)

            def display_loaded_images():
                # Create container for image grid
                grid_container = ctk.CTkFrame(self.images_frame, fg_color="transparent")
                grid_container.pack(fill="both", expand=True, padx=10, pady=10)

                # Configure grid columns
                for i in range(self.grid_width):
                    grid_container.grid_columnconfigure(i, weight=1)

                # Display all loaded images
                for widget_data in self.image_widgets:
                    index = widget_data['index']
                    row = index // self.grid_width
                    col = index % self.grid_width
                    
                    # Create frame for this image
                    img_frame = ctk.CTkFrame(
                        grid_container,
                        fg_color=("gray80", "gray13"),
                        corner_radius=6,
                        border_width=1,
                        border_color=self.colors["border"],
                        width=220,
                        height=220
                    )
                    img_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                    img_frame.grid_propagate(False)
                    
                    # Add image at the top
                    img_label = ctk.CTkLabel(
                        img_frame,
                        image=widget_data['image'],
                        text=""
                    )
                    img_label.place(relx=0.5, rely=0.4, anchor="center")
                    
                    # Add filename label at the bottom
                    name_label = ctk.CTkLabel(
                        img_frame,
                        text=widget_data['name'][:20] + "..." if len(widget_data['name']) > 20 else widget_data['name'],
                        font=ctk.CTkFont(size=11),
                        wraplength=140
                    )
                    name_label.place(relx=0.5, rely=0.9, anchor="center")

            # Start loading images
            load_image(0)

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return

        with open(file_path, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            self.csv_data = list(reader)
            columns = reader.fieldnames

        self.old_lot_dropdown.configure(values=["Select column"] + columns)
        self.new_lot_dropdown.configure(values=["Select column"] + columns)
        self.csv_status.configure(text="✓", text_color="green")
        self.status_label.configure(text="CSV loaded successfully.")

    def upload_images(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path = folder_selected
            self.image_status.configure(text="✓", text_color="green")
            self.status_label.configure(text=f"Selected image folder: {self.folder_path}")

    def select_output_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_folder = folder_selected
            self.output_status.configure(text="✓", text_color="green")
            self.status_label.configure(text=f"Selected output folder: {self.output_folder}")

    def filter_and_rename_images(self):
        if not self.csv_data:
            messagebox.showerror("Error", "No CSV data loaded.")
            return

        if self.old_lot_column.get() == "Select column" or self.new_lot_column.get() == "Select column":
            messagebox.showerror("Error", "Please select both old and new lot columns.")
            return

        if not self.folder_path:
            messagebox.showerror("Error", "Please select an image folder.")
            return

        if not self.output_folder:
            messagebox.showerror("Error", "Please select an output folder.")
            return

        os.makedirs(self.output_folder, exist_ok=True)
        images = [img for img in os.listdir(self.folder_path) 
                 if img.lower().endswith((".jpg", ".jpeg", ".png"))]

        # Create mapping of old to new lot numbers
        lot_mapping = {row[self.old_lot_column.get()].strip(): row[self.new_lot_column.get()].strip() 
                      for row in self.csv_data}

        # Check for duplicates before processing
        duplicates = {}
        for img in images:
            base_name = img.split('-')[0] if '-' in img else os.path.splitext(img)[0]
            if base_name not in duplicates:
                duplicates[base_name] = []
            duplicates[base_name].append(img)

        # Filter out non-duplicates
        duplicates = {k: v for k, v in duplicates.items() if len(v) > 1}

        # If duplicates found, show warning with details
        if duplicates:
            duplicate_msg = "Duplicate lot numbers found:\n\n"
            for lot, files in duplicates.items():
                duplicate_msg += f"Lot {lot} has {len(files)} images:\n"
                for f in files:
                    duplicate_msg += f"  - {f}\n"
            duplicate_msg += "\nDo you want to continue processing?"
            
            if not messagebox.askyesno("Duplicates Found", duplicate_msg, icon='warning'):
                self.action_button.configure(state="normal")
                return

        # Disable the action button during processing
        self.action_button.configure(state="disabled")
        
        # Process images one at a time using after()
        def process_image(index):
            if index >= len(images):
                # All done
                self.progress.set(1.0)
                self.status_label.configure(text=f"Status: Finished. {renamed_count[0]} images renamed.")
                self.action_button.configure(state="normal")
                
                # Show summary of duplicates if any were found
                if duplicates:
                    summary_msg = "Processing complete. Duplicate summary:\n\n"
                    for lot, files in duplicates.items():
                        summary_msg += f"Lot {lot}: {len(files)} images processed\n"
                    messagebox.showinfo("Processing Complete", summary_msg)
                
                # Open the output folder
                if os.name == 'nt':  # Windows
                    os.startfile(self.output_folder)
                else:  # macOS and Linux
                    subprocess.Popen(['open', self.output_folder]) if os.name == 'posix' else subprocess.Popen(['xdg-open', self.output_folder])
                return
            
            img = images[index]
            progress = (index + 1) / len(images)
            self.progress.set(progress)
            self.status_label.configure(text=f"Processing file {index+1} of {len(images)}: {img}")

            # Extract base name without suffix (e.g., "1" from "1-1.jpg")
            base_name = img.split('-')[0] if '-' in img else os.path.splitext(img)[0]
            
            # Find matching lot number using the base name
            matching_old_lot = next((old_lot for old_lot in lot_mapping.keys() 
                                   if old_lot == base_name), None)
            
            if matching_old_lot:
                new_lot = lot_mapping[matching_old_lot]
                # Preserve the suffix for duplicates
                if base_name in duplicates:
                    suffix = img.split('-')[1] if '-' in img else ''
                    ext = os.path.splitext(img)[1]
                    new_name = f"{new_lot}-{suffix if suffix else '1'}{ext}"
                else:
                    # No duplicates, use simple naming
                    ext = os.path.splitext(img)[1]
                    new_name = f"{new_lot}{ext}"    
                    
                src = os.path.join(self.folder_path, img)
                dst = os.path.join(self.output_folder, new_name)

                try:
                    shutil.copy2(src, dst)
                    renamed_count[0] += 1
                    self.history.append({
                        'old_path': src,
                        'new_path': dst,
                        'timestamp': time.time()
                    })
                except Exception as e:
                    self.status_label.configure(text=f"Error renaming {img}: {e}")

            # Schedule the next image processing after 100ms
            self.app.after(100, process_image, index + 1)

        # Initialize counter as a list to make it mutable in the nested function
        renamed_count = [0]
        
        # Start processing the first image
        process_image(0)

    def add_styled_separator(self, parent):
        separator = ctk.CTkFrame(
            parent,
            height=1,
            fg_color=self.colors["border"]
        )
        separator.pack(fill="x", padx=20, pady=15)

    def create_styled_cell(self, parent, text, is_header=False):
        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            border_width=1,
            border_color=self.colors["border"]
        )
        
        label = ctk.CTkLabel(
            frame,
            text=text,
            font=ctk.CTkFont(
                family="Helvetica",
                size=12,
                weight="bold" if is_header else "normal"
            ),
            text_color="white" if is_header else None
        )
        label.pack(padx=10, pady=5)
        
        return frame

    def create_shortcuts_help(self):
        self.shortcuts_window = None
        
        def show_shortcuts_help():
            if self.shortcuts_window is not None:
                return
            
            # Create help window
            self.shortcuts_window = ctk.CTkToplevel(self.app)
            self.shortcuts_window.title("Keyboard Shortcuts")
            self.shortcuts_window.geometry("600x500")
            self.shortcuts_window.resizable(False, False)
            
            # Make window modal
            self.shortcuts_window.transient(self.app)
            self.shortcuts_window.grab_set()
            
            # Create content frame
            content = ctk.CTkFrame(self.shortcuts_window, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Title
            title = ctk.CTkLabel(
                content,
                text="Keyboard Shortcuts",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=self.colors["accent"]
            )
            title.pack(pady=(0, 20))
            
            # Shortcuts sections
            shortcuts = {
                "File Operations": {
                    "Open CSV": "Ctrl + O",
                    "Select Image Folder": "Ctrl + I",
                    "Select Output Folder": "Ctrl + S",
                    "Start Renaming": "Ctrl + R",
                    "Show/Hide Help": "?",
                    "Quit Application": "Ctrl + Q"
                },
                "View Controls": {
                    "Zoom In": "Ctrl + +",
                    "Zoom Out": "Ctrl + -",
                    "Reset Zoom": "Ctrl + 0",
                    "Toggle Fullscreen": "F11"
                }
            }
            
            # Create sections
            for section, items in shortcuts.items():
                # Section frame
                section_frame = ctk.CTkFrame(content, fg_color=("gray85", "gray17"))
                section_frame.pack(fill="x", pady=5)
                
                # Section title
                section_label = ctk.CTkLabel(
                    section_frame,
                    text=section,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=self.colors["accent"]
                )
                section_label.pack(anchor="w", padx=15, pady=10)
                
                # Add shortcuts
                for action, shortcut in items.items():
                    shortcut_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
                    shortcut_frame.pack(fill="x", padx=15, pady=2)
                    
                    action_label = ctk.CTkLabel(
                        shortcut_frame,
                        text=action,
                        font=ctk.CTkFont(size=12),
                        anchor="w"
                    )
                    action_label.pack(side="left")
                    
                    key_label = ctk.CTkLabel(
                        shortcut_frame,
                        text=shortcut,
                        font=ctk.CTkFont(size=12, weight="bold"),
                        text_color=self.colors["accent"]
                    )
                    key_label.pack(side="right")
            
            # Close button
            close_button = ctk.CTkButton(
                content,
                text="Close",
                width=100,
                command=self.close_shortcuts_help,
                font=ctk.CTkFont(size=13),
                fg_color=self.colors["button"],
                hover_color=self.colors["button_hover"]
            )
            close_button.pack(pady=20)
            
            # Bind escape key
            self.shortcuts_window.bind("<Escape>", lambda e: self.close_shortcuts_help())
            
            # Handle window close
            self.shortcuts_window.protocol("WM_DELETE_WINDOW", self.close_shortcuts_help)

        def close_shortcuts_help():
            if self.shortcuts_window is not None:
                self.shortcuts_window.grab_release()
                self.shortcuts_window.destroy()
                self.shortcuts_window = None

        # Add help button to header
        help_button = ctk.CTkButton(
            self.header_frame,
            text="?",
            width=40,
            height=32,
            corner_radius=8,
            command=show_shortcuts_help,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.colors["button"],
            hover_color=self.colors["button_hover"]
        )
        help_button.pack(side="right", padx=10)

        # Bind keyboard shortcuts
        self.app.bind("<Control-o>", lambda e: self.load_csv())
        self.app.bind("<Control-i>", lambda e: self.upload_images())
        self.app.bind("<Control-s>", lambda e: self.select_output_folder())
        self.app.bind("<Control-r>", lambda e: self.filter_and_rename_images())
        self.app.bind("<Control-1>", lambda e: self.tab_view.set("CSV Preview"))
        self.app.bind("<Control-2>", lambda e: self.tab_view.set("Images Preview"))
        self.app.bind("<Control-plus>", lambda e: self.zoom_in())
        self.app.bind("<Control-minus>", lambda e: self.zoom_out())
        self.app.bind("<Control-0>", lambda e: self.reset_zoom())
        self.app.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.app.bind("?", lambda e: show_shortcuts_help())
        self.app.bind("<Escape>", lambda e: close_shortcuts_help())

    def create_landing_page(self):
        # Create landing page frame
        self.landing_page = ctk.CTkFrame(
            self.main_area,
            fg_color="transparent"
        )
        self.landing_page.pack(fill="both", expand=True, padx=40, pady=40)

        # Welcome section
        welcome_frame = ctk.CTkFrame(
            self.landing_page,
            fg_color=("gray85", "gray17"),
            corner_radius=10
        )
        welcome_frame.pack(fill="x", pady=(0, 20))

        # Welcome header
        ctk.CTkLabel(
            welcome_frame,
            text="Welcome to ReNinja",
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"),
            text_color=self.colors["accent"]
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            welcome_frame,
            text="Image Batch Renaming Tool",
            font=ctk.CTkFont(size=14)
        ).pack(pady=(0, 20))

        # Quick start guide
        guide_frame = ctk.CTkFrame(
            self.landing_page,
            fg_color=("gray85", "gray17"),
            corner_radius=10
        )
        guide_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            guide_frame,
            text="Quick Start Guide",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["accent"]
        ).pack(pady=(20, 10))

        steps = [
            ("1. Upload CSV", "Click 'Upload CSV' or press Ctrl+O to load your mapping file"),
            ("2. Select Columns", "Choose the old and new lot number columns from your CSV"),
            ("3. Choose Folders", "Select your image folder and output destination"),
            ("4. Process", "Click 'Filter and Rename Images' to start the batch process")
        ]

        for step, desc in steps:
            step_frame = ctk.CTkFrame(guide_frame, fg_color="transparent")
            step_frame.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(
                step_frame,
                text=step,
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left")
            
            ctk.CTkLabel(
                step_frame,
                text=desc,
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=(10, 0))

    def reset_app(self):
        # Show confirmation dialog
        confirm = messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset the application?\n\nThis will clear all loaded data and selections.",
            icon='warning'
        )
        
        if not confirm:
            return
            
        # Reset variables
        self.csv_data = []
        self.folder_path = ""
        self.output_folder = ""
        self.old_lot_column.set("Select column")
        self.new_lot_column.set("Select column")
        
        # Reset dropdowns
        self.old_lot_dropdown.configure(values=["Select column"])
        self.new_lot_dropdown.configure(values=["Select column"])
        
        # Reset status indicators
        self.csv_status.configure(text="❌", text_color=("gray70", "gray30"))
        self.image_status.configure(text="❌", text_color=("gray70", "gray30"))
        self.output_status.configure(text="❌", text_color=("gray70", "gray30"))
        
        # Reset progress bar
        self.progress.set(0)
        
        # Reset status
        self.status_label.configure(text="Application reset successfully")

    def run(self):
        self.app.mainloop()

    def create_columns_section(self):
        # Column selection frame
        columns_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        columns_frame.pack(fill="x", padx=20, pady=10)
        
        # Old Lot Number selection
        old_lot_label = ctk.CTkLabel(
            columns_frame,
            text="Old Lot Number:",
            font=ctk.CTkFont(size=14)
        )
        old_lot_label.pack(anchor="w")
        
        self.old_lot_dropdown = ctk.CTkOptionMenu(
            columns_frame,
            variable=self.old_lot_column,
            values=["Select column"],
            width=260,  # Match button width
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            anchor="w"  # Align text to the left
        )
        self.old_lot_dropdown.pack(pady=(5, 10), anchor="w")

        # New Lot Number selection
        new_lot_label = ctk.CTkLabel(
            columns_frame,
            text="New Lot Number:",
            font=ctk.CTkFont(size=14)
        )
        new_lot_label.pack(anchor="w")
        
        self.new_lot_dropdown = ctk.CTkOptionMenu(
            columns_frame,
            variable=self.new_lot_column,
            values=["Select column"],
            width=260,  # Match button width
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            anchor="w"  # Align text to the left
        )
        self.new_lot_dropdown.pack(pady=(5, 10), anchor="w")

    def process_mystory_batch(self):
        if not self.mystory_folder or not self.mystory_output:
            messagebox.showerror("Error", "Please select both input and output folders.")
            return

        try:
            sequence_num = int(self.current_sequence.get())
            if sequence_num < 1:
                raise ValueError("Sequence number must be positive")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive number for the sequence.")
            return

        # Get all images from input folder
        images = [f for f in os.listdir(self.mystory_folder) 
                 if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        
        if not images:
            messagebox.showerror("Error", "No images found in input folder.")
            return

        # Sort images naturally first
        def natural_sort_key(s):
            import re
            return [int(text) if text.isdigit() else text.lower()
                   for text in re.split(r'([0-9]+)', os.path.splitext(s)[0])]
        
        images.sort(key=natural_sort_key)

        # Randomly shuffle the images
        random.shuffle(images)

        # Create main output folder if it doesn't exist
        os.makedirs(self.mystory_output, exist_ok=True)

        # Create sequence-specific subfolder
        sequence_folder = os.path.join(self.mystory_output, f"Sequence_{sequence_num}")
        try:
            os.makedirs(sequence_folder, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create sequence folder: {str(e)}")
            return

        # Process images
        count = 1
        # Store the mapping of original to new names for reference
        mapping = []
        
        for img in images:
            ext = os.path.splitext(img)[1]
            new_name = f"{sequence_num}-{count}{ext}"
            src = os.path.join(self.mystory_folder, img)
            dst = os.path.join(sequence_folder, new_name)
            
            try:
                shutil.copy2(src, dst)
                mapping.append(f"{img} → {new_name}")
                count += 1
            except Exception as e:
                messagebox.showerror("Error", f"Error processing {img}: {str(e)}")
                return

        # Create a mapping file in the sequence folder
        mapping_file = os.path.join(sequence_folder, f"sequence_{sequence_num}_mapping.txt")
        with open(mapping_file, 'w', encoding='utf-8') as f:
            f.write(f"Sequence {sequence_num} Image Mapping:\n")
            f.write("Original → New Name\n")
            f.write("-" * 50 + "\n")
            f.write("\n".join(mapping))

        messagebox.showinfo("Success", 
                           f"Processed {count-1} images\n"
                           f"Sequence: {sequence_num}-1 to {sequence_num}-{count-1}\n"
                           f"Folder: Sequence_{sequence_num}\n"
                           f"Mapping file created: sequence_{sequence_num}_mapping.txt")
        
        # Increment sequence number for next batch
        self.current_sequence.set(str(sequence_num + 1))

        # Open sequence folder
        if os.name == 'nt':  # Windows
            os.startfile(sequence_folder)
        else:  # macOS and Linux
            subprocess.Popen(['open', sequence_folder]) if os.name == 'posix' else subprocess.Popen(['xdg-open', sequence_folder])

    def show_mystory_window(self):
        # Create new window
        self.mystory_window = ctk.CTkToplevel(self.app)
        self.mystory_window.title("ReMystery")
        self.mystory_window.geometry("400x500")
        self.mystory_window.resizable(False, False)
        
        # Make window modal
        self.mystory_window.transient(self.app)
        self.mystory_window.grab_set()
        
        # Create content frame
        content = ctk.CTkFrame(self.mystory_window, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            content,
            text="ReMystery Batch Renaming",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["accent"]
        )
        title.pack(pady=(0, 20))
        
        # Input folder selection
        input_frame = ctk.CTkFrame(content, fg_color="transparent")
        input_frame.pack(fill="x", pady=10)
        
        self.mystory_folder = ""
        input_button = ctk.CTkButton(
            input_frame,
            text="Select Input Folder",
            command=self.select_mystory_input,
            height=32,
            corner_radius=8
        )
        input_button.pack(fill="x")
        
        # Output folder selection
        output_frame = ctk.CTkFrame(content, fg_color="transparent")
        output_frame.pack(fill="x", pady=10)
        
        self.mystory_output = ""
        output_button = ctk.CTkButton(
            output_frame,
            text="Select Output Folder",
            command=self.select_mystory_output,
            height=32,
            corner_radius=8
        )
        output_button.pack(fill="x")
        
        # Sequence number entry
        sequence_frame = ctk.CTkFrame(content, fg_color="transparent")
        sequence_frame.pack(fill="x", pady=10)
        
        sequence_label = ctk.CTkLabel(
            sequence_frame,
            text="Starting Sequence Number:",
            font=ctk.CTkFont(size=14)
        )
        sequence_label.pack(anchor="w")
        
        self.current_sequence = ctk.StringVar(value="1")
        sequence_entry = ctk.CTkEntry(
            sequence_frame,
            textvariable=self.current_sequence,
            width=100,
            height=32
        )
        sequence_entry.pack(pady=(5, 0))
        
        # Process button
        process_button = ctk.CTkButton(
            content,
            text="Process Batch",
            command=self.process_mystory_batch,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["success"]
        )
        process_button.pack(pady=20)

    def select_mystory_input(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.mystory_folder = folder_selected
            self.mystory_input_status.configure(text="✓", text_color="green")
            self.mystory_status.configure(text=f"Selected input folder: {folder_selected}")

    def select_mystory_output(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.mystory_output = folder_selected
            self.mystory_output_status.configure(text="✓", text_color="green")
            self.mystory_status.configure(text=f"Selected output folder: {folder_selected}")

    def select_remark_input(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.remark_input_folder = folder_selected
            self.remark_input_status.configure(text="✓", text_color="green")
            self.remark_status.configure(text=f"Selected input folder: {folder_selected}")

    def select_remark_output(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.remark_output_folder = folder_selected
            self.remark_output_status.configure(text="✓", text_color="green")
            self.remark_status.configure(text=f"Selected output folder: {folder_selected}")

    def process_watermarks(self):
        if not hasattr(self, 'remark_input_folder') or not hasattr(self, 'remark_output_folder'):
            messagebox.showerror("Error", "Please select both input and output folders.")
            return

        # Create output directory if it doesn't exist
        os.makedirs(self.remark_output_folder, exist_ok=True)

        # Get all images from input folder
        images = [f for f in os.listdir(self.remark_input_folder) 
                 if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not images:
            messagebox.showerror("Error", "No images found in input folder.")
            return

        # Get watermark text (use default if empty)
        watermark_text = self.watermark_text.get().strip()
        if not watermark_text:
            watermark_text = "Supreme Auction Catalog Image"

        # Disable the action button during processing
        self.remark_action_button.configure(state="disabled")
        
        # Process images one at a time
        def process_image(index):
            if index >= len(images):
                # All done
                self.remark_progress.set(1.0)
                self.remark_status.configure(text=f"Finished. {len(images)} images processed.")
                self.remark_action_button.configure(state="normal")
                
                # Open the output folder
                if os.name == 'nt':  # Windows
                    os.startfile(self.remark_output_folder)
                else:  # macOS and Linux
                    subprocess.Popen(['open', self.remark_output_folder]) if os.name == 'posix' else subprocess.Popen(['xdg-open', self.remark_output_folder])
                return
            
            img_name = images[index]
            progress = (index + 1) / len(images)
            self.remark_progress.set(progress)
            self.remark_status.configure(text=f"Processing {index+1} of {len(images)}: {img_name}")

            try:
                # Open image
                img_path = os.path.join(self.remark_input_folder, img_name)
                img = Image.open(img_path)
                
                # Create a copy of the image for drawing
                watermarked = img.copy()
                
                # Create drawing object
                draw = ImageDraw.Draw(watermarked)
                
                # Get size from settings
                try:
                    size_percent = float(self.watermark_size.get())
                except ValueError:
                    size_percent = 3.5
                
                # Calculate font size based on image size
                font_size = int(min(img.size) * (size_percent / 100))
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                # Get text size
                text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                # Calculate position (bottom right with padding)
                padding = 20
                x = img.width - text_width - padding
                y = img.height - text_height - padding
                
                # Get opacity values
                text_opacity = int(255 * (self.watermark_opacity.get() / 100))
                
                # Draw background if enabled
                if self.bg_enabled.get():
                    bg_color = self.bg_color.get()
                    # Convert hex color to RGB with opacity
                    bg_rgb = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))
                    bg_opacity = int(255 * (self.bg_opacity.get() / 100))
                    bg_bbox = (x - padding, y - padding, x + text_width + padding, y + text_height + padding)
                    draw.rectangle(bg_bbox, fill=bg_rgb + (bg_opacity,))
                
                # Draw shadow and text
                shadow_offset = 2
                draw.text((x + shadow_offset, y + shadow_offset), watermark_text, font=font, fill=(0, 0, 0, text_opacity))
                draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, text_opacity))
                
                # Save the watermarked image
                output_path = os.path.join(self.remark_output_folder, img_name)
                watermarked.save(output_path, quality=95)

            except Exception as e:
                self.remark_status.configure(text=f"Error processing {img_name}: {str(e)}")
                messagebox.showerror("Error", f"Error processing {img_name}: {str(e)}")
                self.remark_action_button.configure(state="normal")
                return

            # Schedule the next image processing
            self.app.after(100, process_image, index + 1)

        # Start processing the first image
        process_image(0)

    def check_for_updates(self):
        has_update, latest_version, download_url = UpdateChecker.check_for_updates()
        if has_update:
            UpdateNotification(self, latest_version, download_url)

if __name__ == "__main__":
    app = ImageRenamerApp()
    app.run()
