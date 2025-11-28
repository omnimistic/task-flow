import customtkinter as ctk
import tkinter as tk
import json
import os
import pyglet
from datetime import datetime

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


font_path = 'font/Inter-4.1/Inter-ExtraBold.ttf'


if os.path.exists(font_path):
    try:
        
        pyglet.font.add_file(font_path)
        font_family_variable = "Inter"
        print(f"Successfully loaded custom font: {font_family_variable}")
    except Exception as e:
        print(f"Could not load custom font. Error: {e}")
        font_family_variable = "Arial"
else:
    print(f"Font file not found at {font_path}. Using Arial.")
    font_family_variable = "Arial"


## Dynamic Scrollable Frame Class
class DynamicScrollableFrame:
    """A frame with a dynamic scrollbar that only appears when needed."""
    def __init__(self, parent, orientation="vertical", bg_color="#1e1e2e"):
        self.parent = parent
        self.orientation = orientation
        
        # Create canvas
        self.canvas = tk.Canvas(parent, bg=bg_color, highlightthickness=0)
        
        # Create scrollbar
        self.scrollbar = ctk.CTkScrollbar(
            parent,
            orientation=orientation,
            command=self.canvas.yview if orientation == "vertical" else self.canvas.xview
        )
        
        if orientation == "vertical":
            self.canvas.configure(yscrollcommand=self.scrollbar.set)
        else:
            self.canvas.configure(xscrollcommand=self.scrollbar.set)
        
        # Create inner frame
        self.inner_frame = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        
        # Bind to update scrollbar
        self.inner_frame.bind("<Configure>", self.update_scrollbar)
        
    def pack(self, **kwargs):
        """Pack the canvas."""
        self.canvas.pack(**kwargs)
    
    def update_scrollbar(self, event=None):
        """Show/hide scrollbar based on content size."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        if self.orientation == "vertical":
            canvas_height = self.canvas.winfo_height()
            content_height = self.inner_frame.winfo_reqheight()
            
            if content_height > canvas_height:
                self.scrollbar.pack(side="right", fill="y", before=self.canvas)
            else:
                self.scrollbar.pack_forget()
        else:
            canvas_width = self.canvas.winfo_width()
            content_width = self.inner_frame.winfo_reqwidth()
            
            if content_width > canvas_width:
                self.scrollbar.pack(side="bottom", fill="x", before=self.canvas)
            else:
                self.scrollbar.pack_forget()


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
        self.render_board()
    
    # --- UI Setup ---
    
    def setup_ui(self):
        self.top_frame = ctk.CTkFrame(self.root, height=60, corner_radius=0)
        self.top_frame.pack(fill="x", side="top")
        
        title_label = ctk.CTkLabel(
            self.top_frame, 
            text="📋 TaskFlow",
            font=(self.font_family, 20, "bold")
        )
        title_label.pack(side="left", padx=20, pady=10)
        
        board_label = ctk.CTkLabel(
            self.top_frame,
            text="Board:",
            font=(self.font_family, 12)
        )
        board_label.pack(side="left", padx=(50, 10), pady=10)
        
        self.board_var = ctk.StringVar(value="No boards")
        self.board_dropdown = ctk.CTkComboBox(
            self.top_frame,
            variable=self.board_var,
            values=["No boards"],
            width=200,
            state="readonly",
            command=self.board_selected
        )
        self.board_dropdown.pack(side="left", padx=5, pady=10)

        self.board_name_label = ctk.CTkLabel(
            self.top_frame,
            text="",
            font=(self.font_family, 14, "bold")
        )
        self.board_name_label.pack(side="left", padx=(0, 20), pady=10)
        self.board_name_label.bind("<Double-Button-1>", self.rename_board_dialog)

        # Create the Button Factory instance
        button_factory = CTkButtonFactory(self.top_frame, self.font_family)

        # 1. Delete Board button using the factory
        delete_board_btn = button_factory.create_button(
            text="- Delete Board",
            command=self.delete_board_dialog,
            fg_color="#f38ba8",
            hover_color="#d16d87"
        )
        delete_board_btn.pack(side="left", padx=5, pady=10)

        # 2. New Board button using the factory
        new_board_btn = button_factory.create_button(
            text="+ New Board",
            command=self.create_board_dialog
        )
        new_board_btn.pack(side="left", padx=5, pady=10)

        # 3. New List button using the factory
        new_list_btn = button_factory.create_button(
            text="+ New List",
            command=self.create_list_dialog
        )
        new_list_btn.pack(side="left", padx=5, pady=10)

        # Main content area with dynamic horizontal scrollbar
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Use DynamicScrollableFrame for horizontal scrolling
        self.main_scrollable = DynamicScrollableFrame(main_frame, orientation="horizontal")
        self.main_scrollable.pack(side="top", fill="both", expand=True)
        
        # Store reference to the lists container
        self.lists_container = self.main_scrollable.inner_frame
    
    def board_selected(self, choice):
        """Updates the current_board when a selection is made in the dropdown."""
        if choice in self.boards:
            self.current_board = choice
            self.board_name_label.configure(text=choice)
            self.save_data()
            self.render_board()
    
    def rename_board_dialog(self, event=None):
        if not self.current_board or self.current_board == "No boards":
            return
        dialog = ctk.CTkInputDialog(
            text="Enter new board name:",
            title="Rename Board",
            entry_text=self.current_board
        )
        new_name = dialog.get_input()
        if new_name and new_name.strip() and new_name != self.current_board and new_name not in self.boards:
            board_data = self.boards.pop(self.current_board)
            self.boards[new_name] = board_data
            self.current_board = new_name
            self.board_name_label.configure(text=new_name)
            self.board_var.set(new_name)
            self.save_data()
            self.board_dropdown.configure(values=list(self.boards.keys()))
            self.render_board()
    
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
        self.render_board()
    
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
            
            if self.current_board is None or self.current_board not in board_names:
                 self.current_board = board_names[0]
                 
            self.board_var.set(self.current_board)
            self.board_name_label.configure(text=self.current_board)
        else:
            self.board_dropdown.configure(values=["No boards"])
            self.board_var.set("No boards")
            self.current_board = None
            self.board_name_label.configure(text="")
    
    def delete_board_dialog(self):
        if not self.current_board or self.current_board == "No boards":
            print("Cannot delete: No board is currently selected.")
            return
        
        dialog = ctk.CTkInputDialog(
            text=f"Type '{self.current_board}' to confirm deletion of the board:",
            title="Delete Board"
        )
        confirmation = dialog.get_input()
        
        if confirmation == self.current_board:
            deleted_board = self.current_board
            
            del self.boards[deleted_board]
            
            remaining_boards = list(self.boards.keys())
            self.current_board = remaining_boards[0] if remaining_boards else None
            
            self.save_data()
            self.update_board_dropdown()
            self.render_board()
    
    def create_list(self, name):
        if not self.current_board or self.current_board == "No boards":
            return
        
        board = self.boards[self.current_board]
        
        if name in board["lists"]:
            return
        
        board["lists"][name] = {"cards": []}
        self.save_data()
        self.render_board()
    
    def create_list_dialog(self):
        if not self.current_board or self.current_board == "No boards":
            print("Cannot create list: No board is currently selected.")
            return
        
        dialog = ctk.CTkInputDialog(
            text="Enter list name:",
            title="New List"
        )
        name = dialog.get_input()
        
        if name:
            self.create_list(name)
    

    def start_edit_list_name(self, label, list_name, header):
        current = label.cget("text")
        label.destroy()
        entry = ctk.CTkEntry(header, font=(self.font_family, 14, "bold"))
        entry.insert(0, current)
        entry.pack(side="left", padx=10, pady=8)
        entry.focus()
        def save(event=None):
            new_name = entry.get().strip()
            entry.destroy()
            board = self.boards[self.current_board]
            renamed = False
            if new_name and new_name != list_name and new_name not in board["lists"]:
                list_data = board["lists"].pop(list_name)
                board["lists"][new_name] = list_data
                renamed = True
                self.save_data()
            self.render_board()
        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)

    def render_list(self, list_name, list_data):
        list_frame = ctk.CTkFrame(
            self.lists_container,
            width=280,
            corner_radius=10,
            fg_color="#2b2d3a"
        )
        list_frame.pack(side="left", padx=10, pady=10, fill="both", anchor="n")
        
        # List header
        header = ctk.CTkFrame(list_frame, fg_color="#3d3f4f", corner_radius=8, height=40)
        header.pack(fill="x", padx=5, pady=5)
        header.pack_propagate(False)

        list_label = ctk.CTkLabel(
            header,
            text=list_name,
            font=(self.font_family, 14, "bold")
        )
        list_label.pack(side="left", padx=10, pady=8)
        list_label.bind("<Double-Button-1>", lambda event: self.start_edit_list_name(list_label, list_name, header))

        # Delete list button
        ctk.CTkButton(
            header,
            text="×",
            width=30,
            height=30,
            font=(self.font_family, 20),
            fg_color="#f38ba8",
            hover_color="#d16d87",
            command=lambda: self.delete_list(list_name)
        ).pack(side="right", padx=5)

        # Add card button at bottom - PACK FIRST
        ctk.CTkButton(
            list_frame,
            text="+ Add Card",
            fg_color="#313244",
            hover_color="#45475a",
            command=lambda: self.create_card_dialog(list_name)
        ).pack(side="bottom", fill="x", padx=5, pady=5)

        # Cards container with dynamic vertical scrollbar
        cards_scrollable = DynamicScrollableFrame(list_frame, orientation="vertical", bg_color="#2b2d3a")
        cards_scrollable.pack(fill="both", expand=True, padx=5, pady=5)

        # Render each card
        for idx, card in enumerate(list_data["cards"]):
            self.render_card(cards_scrollable.inner_frame, list_name, card, idx)
    

    def render_board(self):
        # Clear existing lists
        for widget in self.lists_container.winfo_children():
            widget.destroy()
        
        if not self.current_board or self.current_board == "No boards":
            return
        
        board = self.boards[self.current_board]
        
        for list_name, list_data in board["lists"].items():
            self.render_list(list_name, list_data)
    

    def delete_list(self, list_name):
        dialog = ctk.CTkInputDialog(
            text=f"Type '{list_name}' to confirm deletion:",
            title="Delete List"
        )
        confirmation = dialog.get_input()
        
        if confirmation == list_name:
            board = self.boards[self.current_board]
            del board["lists"][list_name]
            self.save_data()
            self.render_board()
    
    def create_card(self, list_name, title):
        board = self.boards[self.current_board]
        card = {
            "title": title,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        board["lists"][list_name]["cards"].append(card)
        self.save_data()
        self.render_board()
    
    def create_card_dialog(self, list_name):
        dialog = ctk.CTkInputDialog(
            text="Enter card title:",
            title="New Card"
        )
        title = dialog.get_input()
        
        if title:
            self.create_card(list_name, title)
    
    def start_edit_card_title(self, title_label, list_name, idx, card_frame):
        current = title_label.cget("text")
        title_label.destroy()
        entry = ctk.CTkEntry(card_frame, font=(self.font_family, 14), width=260)
        entry.insert(0, current)
        entry.pack(fill="x", padx=10, pady=(10, 5))
        entry.focus()
        def save(event=None):
            new_title = entry.get().strip()
            entry.destroy()
            if new_title:
                self.boards[self.current_board]["lists"][list_name]["cards"][idx]["title"] = new_title
                self.save_data()
            self.render_board()
        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)

    def render_card(self, parent, list_name, card, idx):
        card_frame = ctk.CTkFrame(
            parent,
            corner_radius=8,
            fg_color="#313244",
            height=70
        )
        card_frame.pack(fill="x", padx=5, pady=3)
        card_frame.pack_propagate(False)
        
        # Card title
        title_label = ctk.CTkLabel(
            card_frame,
            text=card["title"],
            font=(self.font_family, 14),
            wraplength=260,
            anchor="w",
            justify="left"
        )
        title_label.pack(fill="x", padx=12, pady=(12, 5))
        title_label.bind("<Double-Button-1>", lambda e: self.start_edit_card_title(title_label, list_name, idx, card_frame))
        
        # Card date
        ctk.CTkLabel(
            card_frame,
            text=card["created"],
            font=(self.font_family, 12),
            text_color="#6c7086",
            anchor="w"
        ).pack(fill="x", padx=12, pady=(0, 12))


if __name__ == "__main__":
    root = ctk.CTk()
    app = TaskBoard(root)
    root.mainloop()
