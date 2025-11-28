import customtkinter as ctk
import tkinter as tk #for the dynamic scrollbar. i just couldn't live with the static one in ctk
import json
import os
from tkextrafont import Font # Import the library to load fonts dynamically
from pathlib import Path

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ------------------------------------------------------------------
# DYNAMIC FONT LOADING LOGIC
# ------------------------------------------------------------------

# 1. Specify the path to the font file
font_path = 'font\Inter-4.1\InterVariable.ttf'

# 2. Define a name for the font that Tkinter will use internally
font_var_name = "Inter_Dynamic" 

# 3. Try to load the font dynamically
try:
    # Font is loaded into memory without system installation
    Font(file=str(font_path), family=font_var_name)
    
    # If successful, this is the name we use for our variable
    font_family_variable = font_var_name 
    print(f"✅ Successfully loaded custom font: {font_family_variable}")

except Exception as e:
    print(f"⚠️ Could not load custom font from {font_path}. Falling back to Helvetica.")
    print(f"Error details: {e}")
    # Fallback to a common system font if loading fails
    font_family_variable = "Helvetica"



## Button Factory Class
class CTkButtonFactory:
    """A factory class to create and configure CTkButtons."""
    def __init__(self, master, font_family):
        self.master = master
        self.font = (font_family, 16)
        
    def create_button(self, text, command, fg_color=None, hover_color=None):
        """Creates and returns a customtkinter button."""
        button = ctk.CTkButton(
            self.master,
            text=text,
            width=120,
            height=35,
            font=self.font,
            command=command,
            fg_color=fg_color,
            hover_color=hover_color
        )
        return button

## TaskBoard Class
class TaskBoard:
    def __init__(self, root):
        """#__init__ method is a method that gets called 
        when an object is created from a class 
        and allows the class to initialize the attributes of the class."""
        self.root = root
        self.root.title("TaskFlow - Task Manager")
        self.root.geometry("1200x700")
        
        self.font_family = font_family_variable 
        
        # Data storage
        self.data_file = "taskflow_data.json"
        self.boards = {}
        self.current_board = None
        
        self.load_data()
        
        self.setup_ui()
            
        if not self.boards:
            self.create_board("My First Board")
        
        self.update_board_dropdown()
    
    # --- UI Setup ---
    
    def setup_ui(self):
        top_frame = ctk.CTkFrame(self.root, height=60, corner_radius=0)
        top_frame.pack(fill="x", side="top")
        
        title_label = ctk.CTkLabel(
            top_frame, 
            text="📋 TaskFlow",
            font=(self.font_family, 20, "bold")
        )
        title_label.pack(side="left", padx=20, pady=10)
        
        board_label = ctk.CTkLabel(
            top_frame,
            text="Board:",
            font=(self.font_family, 12)
        )
        board_label.pack(side="left", padx=(50, 10), pady=10)
        
        self.board_var = ctk.StringVar(value="No boards")
        self.board_dropdown = ctk.CTkComboBox(
            top_frame,
            variable=self.board_var,
            values=["No boards"], # Default values
            width=200,
            state="readonly",
            command=self.board_selected # Add command to update current board on selection
        )
        self.board_dropdown.pack(side="left", padx=5, pady=10)

        # Create the Button Factory instance
        button_factory = CTkButtonFactory(top_frame, self.font_family)

        # 1. Delete Board button using the factory
        delete_board_btn = button_factory.create_button(
            text="- Delete Board",
            command=self.delete_board_dialog,
            fg_color="#f38ba8", # Custom color for delete
            hover_color="#d16d87"
        )
        delete_board_btn.pack(side="left", padx=5, pady=10)

        # 2. New Board button using the factory
        new_board_btn = button_factory.create_button(
            text="+ New Board",
            command=self.create_board_dialog
            # Uses default colors
        )
        new_board_btn.pack(side="left", padx=5, pady=10)

        # 3. New List button using the factory
        new_list_btn = button_factory.create_button(
            text="+ New List",
            command=lambda: print("New List clicked") # Placeholder command
        )
        new_list_btn.pack(side="left", padx=5, pady=10)

        # Main content area
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create canvas for horizontal scrolling
        self.canvas = tk.Canvas(main_frame, bg="#1e1e2e", highlightthickness=0)
        self.canvas.pack(side="top", fill="both", expand=True)

        # Horizontal scrollbar (hidden by default)
        self.h_scrollbar = ctk.CTkScrollbar(
            main_frame,
            orientation="horizontal",
            command=self.canvas.xview
        )
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set)

        # Frame inside canvas to hold lists
        self.lists_container = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.lists_container,
            anchor="nw"
        )

        # Bind to update scrollbar visibility
        self.lists_container.bind("<Configure>", self.update_scrollbar)
    
    def board_selected(self, choice):
        """Updates the current_board when a selection is made in the dropdown."""
        if choice in self.boards:
            self.current_board = choice
        
    def update_scrollbar(self, event=None):
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Show/hide scrollbar based on content width
        canvas_width = self.canvas.winfo_width()
        content_width = self.lists_container.winfo_reqwidth()
        
        if content_width > canvas_width:
            self.h_scrollbar.pack(side="bottom", fill="x", before=self.canvas)
        else:
            self.h_scrollbar.pack_forget()
        
    
    # --- Data Management ---
    
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.boards = data.get('boards', {})
                    self.current_board = data.get('current_board')
            except:
                self.boards = {}
                self.current_board = None

    def save_data(self):
        data = {
            'boards': self.boards,
            'current_board': self.current_board
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # --- Board Methods ---
    
    def create_board(self, name):
        if name in self.boards:
            return
        
        self.boards[name] = {"lists": {}}
        self.current_board = name
        self.save_data()
        self.update_board_dropdown()
    
    def create_board_dialog(self):
        dialog = ctk.CTkInputDialog(
            text="Enter board name:",
            title="New Board"
        )
        name = dialog.get_input()
        
        if name:
            self.create_board(name)
    
    def update_board_dropdown(self):
        board_names = list(self.boards.keys())
        
        if board_names:
            self.board_dropdown.configure(values=board_names)
            
            # Ensure the current_board is valid, or default to the first board
            if self.current_board is None or self.current_board not in board_names:
                 self.current_board = board_names[0]
                 
            self.board_var.set(self.current_board)
        else:
            self.board_dropdown.configure(values=["No boards"])
            self.board_var.set("No boards")
            self.current_board = None # Explicitly set to None when no boards exist
    
    def delete_board_dialog(self):
        # Check to ensure a valid board is selected before opening the dialog
        if not self.current_board or self.current_board == "No boards":
            print("Cannot delete: No board is currently selected.")
            return
        
        # The dialog now correctly uses the value of self.current_board
        dialog = ctk.CTkInputDialog(
            text=f"Type '{self.current_board}' to confirm deletion of the board:",
            title="Delete Board"
        )
        confirmation = dialog.get_input()
        
        if confirmation == self.current_board:
            # 1. Store the board being deleted
            deleted_board = self.current_board
            
            # 2. Delete the board
            del self.boards[deleted_board]
            
            # 3. Determine the next current board
            remaining_boards = list(self.boards.keys())
            self.current_board = remaining_boards[0] if remaining_boards else None
            
            # 4. Save and update UI
            self.save_data()
            self.update_board_dropdown()


if __name__ == "__main__":
    root = ctk.CTk()
    app = TaskBoard(root)
    root.mainloop()