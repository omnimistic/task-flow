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
        
        # Drag and drop
        self.dragged_item = None
        self.drag_data = None
        self.offset_x = None
        self.offset_y = None
        self.drag_start_x_root = None
        self.drag_start_y_root = None

        self.resize_data = None
        
        # Permanent offset adjustment - HARDCODED VALUES
        self.ghost_offset_x = -315
        self.ghost_offset_y = -109
        
        # Constants for drag drop
        self.HEADER_HEIGHT = 50
        self.CARD_HEIGHT = 80
        self.LIST_WIDTH = 300
        
        # Store references to list frames for partial updates
        self.list_frames = {}
        self.list_scrollables = {}
        
        self.load_data()
        
        self.setup_ui()
            
        if not self.boards:
            self.create_board("My First Board")
        
        self.update_board_dropdown()
        self.render_board()
    
    def create_card_ghost(self, card):
        ghost = ctk.CTkFrame(
            self.root,
            corner_radius=8,
            fg_color="#45475a",
            height=70,
            width=260
        )
        ghost.pack_propagate(False)
        
        # Card top frame for title (no delete in ghost)
        card_top = ctk.CTkFrame(ghost, fg_color="transparent", height=30)
        card_top.pack(fill="x", padx=10, pady=(10, 0))
        card_top.pack_propagate(False)
        
        # Card title
        title_label = ctk.CTkLabel(
            card_top,
            text=card["title"],
            font=(self.font_family, 14),
            wraplength=240,
            anchor="w",
            justify="left"
        )
        title_label.pack(side="left", fill="both", expand=True, padx=(5, 5), pady=2)
        
        # Card date
        date_label = ctk.CTkLabel(
            ghost,
            text=card["created"],
            font=(self.font_family, 12),
            text_color="#6c7086",
            anchor="w"
        )
        date_label.pack(fill="x", padx=10, pady=(5, 10))
        
        return ghost
    
    def create_list_ghost(self, list_name, list_data):
        num_cards = len(list_data["cards"])
        ghost = ctk.CTkFrame(
            self.root,
            width=280,
            corner_radius=10,
            fg_color="#45475a",
            height=80
        )
        ghost.pack_propagate(False)
        
        # Header
        header = ctk.CTkFrame(ghost, fg_color="#5a5c6e", corner_radius=8, height=40)
        header.pack(fill="x", padx=5, pady=5)
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text=list_name,
            font=(self.font_family, 14, "bold")
        ).pack(side="left", padx=10, pady=8)
        
        # Cards count
        ctk.CTkLabel(
            ghost,
            text=f"{num_cards} cards",
            font=(self.font_family, 10),
            text_color="#6c7086"
        ).pack(pady=5)
        
        return ghost
    
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
        
        # Bind drag events to root
        self.root.bind("<B1-Motion>", self.on_drag_motion)
        self.root.bind("<ButtonRelease-1>", self.on_drop)

    
    def start_drag(self, event, widget, list_name, idx=None):
        if self.dragged_item:
            return
        
        drag_type = 'card' if idx is not None else 'list'
        self.drag_data = {
            'type': drag_type,
            'list_name': list_name,
            'idx': idx
        }
        
        # Get widget's absolute screen position BEFORE any changes
        widget_screen_x = widget.winfo_rootx()
        widget_screen_y = widget.winfo_rooty()
        
        # Get mouse screen position
        mouse_screen_x = self.root.winfo_pointerx()
        mouse_screen_y = self.root.winfo_pointery()
        
        # Calculate offset (mouse relative to widget)
        self.offset_x = mouse_screen_x - widget_screen_x
        self.offset_y = mouse_screen_y - widget_screen_y
        
        # Store for drag detection
        self.drag_start_x_root = mouse_screen_x
        self.drag_start_y_root = mouse_screen_y
        
        # Forget current packing
        widget.pack_forget()
        
        board = self.boards[self.current_board]
        self.dragged_item = None
        
        if drag_type == 'card':
            card = board['lists'][list_name]['cards'].pop(idx)
            self.drag_data['card'] = card
            self.dragged_item = self.create_card_ghost(card)
        else:
            list_data = board['lists'].pop(list_name)
            self.drag_data['list_data'] = list_data
            self.dragged_item = self.create_list_ghost(list_name, list_data)
        
        # Place ghost at widget's screen position (converted to root-relative)
        root_screen_x = self.root.winfo_rootx()
        root_screen_y = self.root.winfo_rooty()
        
        ghost_x = widget_screen_x - root_screen_x
        ghost_y = widget_screen_y - root_screen_y
        
        self.dragged_item.place(x=ghost_x, y=ghost_y)
        self.dragged_item.lift()

    def on_drag_motion(self, event):
        if self.dragged_item:
            # Get current mouse screen position
            mouse_screen_x = self.root.winfo_pointerx()
            mouse_screen_y = self.root.winfo_pointery()
            
            # Get root's screen position
            root_screen_x = self.root.winfo_rootx()
            root_screen_y = self.root.winfo_rooty()
            
            # Calculate ghost position: (mouse - root) - offset
            ghost_x = (mouse_screen_x - root_screen_x) - self.offset_x
            ghost_y = (mouse_screen_y - root_screen_y) - self.offset_y
            
            self.dragged_item.place(x=ghost_x, y=ghost_y)
    
    def on_drop(self, event):
        if not self.dragged_item:
            return
        
        self.dragged_item.place_forget()
        self.dragged_item.destroy()
        
        dx = abs(event.x_root - self.drag_start_x_root)
        dy = abs(event.y_root - self.drag_start_y_root)
        
        if dx < 10 and dy < 10:
            # Not dragged far enough, put back
            board = self.boards[self.current_board]
            if self.drag_data['type'] == 'card':
                source_list = self.drag_data['list_name']
                idx = self.drag_data['idx']
                board['lists'][source_list]['cards'].insert(idx, self.drag_data['card'])
            else:
                source_list = self.drag_data['list_name']
                board['lists'][source_list] = self.drag_data['list_data']
            self.save_data()
            
            # Only re-render affected list
            if self.drag_data['type'] == 'card':
                self.render_list_cards(source_list)
            else:
                self.render_board()
        else:
            # Process drop
            drag_type = self.drag_data['type']
            board = self.boards[self.current_board]
            mouse_x = event.x_root
            mouse_y = event.y_root
            
            if drag_type == 'card':
                source_list = self.drag_data['list_name']
                card = self.drag_data['card']
                
                target_list = None
                insertion_idx = 0
                
                for lf in self.lists_container.winfo_children():
                    if lf.winfo_ismapped():
                        lx = lf.winfo_rootx()
                        ly = lf.winfo_rooty()
                        lw = lf.winfo_width()
                        lh = lf.winfo_height()
                        if lx <= mouse_x <= lx + lw and ly <= mouse_y <= ly + lh:
                            target_list = lf.list_name
                            cards_start_y = ly + self.HEADER_HEIGHT
                            rel_y = max(0, mouse_y - cards_start_y)
                            insertion_idx = min(len(board['lists'][target_list]['cards']), int(rel_y / self.CARD_HEIGHT))
                            break
                
                if target_list:
                    board['lists'][target_list]['cards'].insert(insertion_idx, card)
                    self.save_data()
                    
                    # Only re-render the two affected lists
                    if source_list == target_list:
                        self.render_list_cards(source_list)
                    else:
                        self.render_list_cards(source_list)
                        self.render_list_cards(target_list)
                else:
                    # Put back to source
                    board['lists'][source_list]['cards'].insert(self.drag_data['idx'], card)
                    self.save_data()
                    self.render_list_cards(source_list)
                
            elif drag_type == 'list':
                source_list = self.drag_data['list_name']
                list_data = self.drag_data['list_data']
                
                container_x = self.lists_container.winfo_rootx()
                rel_x = max(0, mouse_x - container_x)
                target_idx = int(rel_x / self.LIST_WIDTH)
                num_lists = len(board['lists'])
                if target_idx > num_lists:
                    target_idx = num_lists
                
                ordered_lists = list(board['lists'].keys())
                ordered_lists.insert(target_idx, source_list)
                
                new_lists = {}
                for ln in ordered_lists:
                    if ln == source_list:
                        new_lists[ln] = list_data
                    else:
                        new_lists[ln] = board['lists'][ln]
                board['lists'] = new_lists
                self.save_data()
                self.render_board()
        
        self.dragged_item = None
        self.drag_data = None
        self.offset_x = None
        self.offset_y = None
        self.drag_start_x_root = None
        self.drag_start_y_root = None
    
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

    def render_list_cards(self, list_name):
        """Re-render only the cards in a specific list"""
        if list_name not in self.list_scrollables:
            return
        
        # Clear existing cards
        scrollable = self.list_scrollables[list_name]
        for widget in scrollable.inner_frame.winfo_children():
            widget.destroy()
        
        # Re-render cards
        board = self.boards[self.current_board]
        if list_name in board["lists"]:
            list_data = board["lists"][list_name]
            for idx, card in enumerate(list_data["cards"]):
                self.render_card(scrollable.inner_frame, list_name, card, idx)

    def render_list(self, list_name, list_data):
        list_frame = ctk.CTkFrame(
            self.lists_container,
            width=280,
            corner_radius=10,
            fg_color="#2b2d3a"
        )
        list_frame.pack(side="left", padx=10, pady=10, fill="both", anchor="n")
        list_frame.list_name = list_name  # For drop detection
        
        # Store reference
        self.list_frames[list_name] = list_frame
        
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

        # Bind drag for list on header
        header.bind("<Button-1>", lambda e, ln=list_name: self.start_drag(e, list_frame, ln))

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
        
        # Store reference
        self.list_scrollables[list_name] = cards_scrollable

        # Render each card
        for idx, card in enumerate(list_data["cards"]):
            self.render_card(cards_scrollable.inner_frame, list_name, card, idx)
    

    def render_board(self):
        # Clear existing lists
        for widget in self.lists_container.winfo_children():
            widget.destroy()
        
        # Clear references
        self.list_frames = {}
        self.list_scrollables = {}
        
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
        # Only re-render this list's cards
        self.render_list_cards(list_name)
    
    def create_card_dialog(self, list_name):
        dialog = ctk.CTkInputDialog(
            text="Enter card title:",
            title="New Card"
        )
        title = dialog.get_input()
        
        if title:
            self.create_card(list_name, title)
    
    def delete_card_dialog(self, list_name, idx):
        dialog = ctk.CTkInputDialog(
            text="Type 'confirm' to confirm deletion of the card:",
            title="Delete Card"
        )
        confirmation = dialog.get_input()
        
        if confirmation == "confirm":
            board = self.boards[self.current_board]
            del board["lists"][list_name]["cards"][idx]
            self.save_data()
            # Only re-render this list's cards
            self.render_list_cards(list_name)

    def start_edit_card_title(self, title_label, list_name, idx, card_top):
        current = title_label.cget("text")
        title_label.destroy()
        entry = ctk.CTkEntry(card_top, font=(self.font_family, 14), width=260)
        entry.insert(0, current)
        entry.pack(side="left", fill="both", expand=True, padx=(5, 5), pady=2)
        entry.focus()
        def save(event=None):
            new_title = entry.get().strip()
            entry.destroy()
            if new_title:
                self.boards[self.current_board]["lists"][list_name]["cards"][idx]["title"] = new_title
                self.save_data()
            # Only re-render this list's cards
            self.render_list_cards(list_name)
        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)

    def render_card(self, parent, list_name, card, idx):
        # Get card dimensions if stored
        card_width = card.get('width', 260)
        card_height = card.get('height', None)  # None = auto height
        
        card_frame = ctk.CTkFrame(
            parent,
            corner_radius=8,
            fg_color="#313244",
            width=card_width
        )
        
        if card_height:
            card_frame.configure(height=card_height)
            card_frame.pack_propagate(False)
        else:
            card_frame.pack_propagate(True)
        
        card_frame.pack(fill="x", padx=5, pady=3)
        
        # Card top frame for title and delete button
        card_top = ctk.CTkFrame(card_frame, fg_color="transparent")
        card_top.pack(fill="x", padx=10, pady=(10, 0))
        
        # Card title with dynamic wrapping
        title_label = ctk.CTkLabel(
            card_top,
            text=card["title"],
            font=(self.font_family, 14),
            wraplength=card_width - 60,
            anchor="w",
            justify="left"
        )
        title_label.pack(side="left", fill="both", expand=True, padx=(5, 5), pady=2)
        title_label.bind("<Double-Button-1>", lambda e: self.start_edit_card_title(title_label, list_name, idx, card_top))
        
        # Delete card button
        ctk.CTkButton(
            card_top,
            text="×",
            width=25,
            height=25,
            font=(self.font_family, 16),
            fg_color="#f38ba8",
            hover_color="#d16d87",
            command=lambda: self.delete_card_dialog(list_name, idx)
        ).pack(side="right", padx=5, pady=2)
        
        # Bottom frame for date and handles
        card_bottom = ctk.CTkFrame(card_frame, fg_color="transparent")
        card_bottom.pack(fill="x", padx=10, pady=(5, 5))
        
        # Card date
        ctk.CTkLabel(
            card_bottom,
            text=card["created"],
            font=(self.font_family, 12),
            text_color="#6c7086",
            anchor="w"
        ).pack(side="left")
        
        # Resize handle (bottom-right corner)
        resize_handle = ctk.CTkLabel(
            card_bottom,
            text="⋱",
            font=(self.font_family, 16, "bold"),
            text_color="#89b4fa",
            cursor="size_nw_se"
        )
        resize_handle.pack(side="right", padx=2)
        resize_handle.bind("<Button-1>", lambda e: self.start_resize_card(e, card_frame, list_name, idx, card))
        
        # Drag handle
        drag_handle = ctk.CTkLabel(
            card_bottom,
            text="///",
            font=(self.font_family, 12, "bold"),
            text_color="#6c7086",
            cursor="hand2"
        )
        drag_handle.pack(side="right", padx=5)
        drag_handle.bind("<Button-1>", lambda e, ln=list_name, i=idx: self.start_drag(e, card_frame, ln, i))

    def start_resize_card(self, event, card_frame, list_name, idx, card):
        """Start resizing a card"""
        self.resize_data = {
            'card_frame': card_frame,
            'list_name': list_name,
            'idx': idx,
            'card': card,
            'start_x': event.x_root,
            'start_y': event.y_root,
            'start_width': card.get('width', 260),
            'start_height': card.get('height', card_frame.winfo_height())
        }
        self.root.bind("<B1-Motion>", self.on_resize_card_motion)
        self.root.bind("<ButtonRelease-1>", self.on_resize_card_end)

    def on_resize_card_motion(self, event):
        """Handle card resize motion - both directions based on mouse movement"""
        if hasattr(self, 'resize_data'):
            # Calculate deltas
            delta_x = event.x_root - self.resize_data['start_x']
            delta_y = event.y_root - self.resize_data['start_y']
            
            # Apply horizontal resize if mouse moved horizontally
            if abs(delta_x) > 0:
                new_width = max(150, self.resize_data['start_width'] + delta_x)
                self.resize_data['card_frame'].configure(width=new_width)
            
            # Apply vertical resize if mouse moved vertically
            if abs(delta_y) > 0:
                new_height = max(70, self.resize_data['start_height'] + delta_y)
                self.resize_data['card_frame'].configure(height=new_height)
                self.resize_data['card_frame'].pack_propagate(False)

    def on_resize_card_end(self, event):
        """End card resize"""
        if hasattr(self, 'resize_data'):
            list_name = self.resize_data['list_name']
            idx = self.resize_data['idx']
            
            # Calculate final dimensions
            delta_x = event.x_root - self.resize_data['start_x']
            delta_y = event.y_root - self.resize_data['start_y']
            
            new_width = max(150, self.resize_data['start_width'] + delta_x)
            new_height = max(70, self.resize_data['start_height'] + delta_y)
            
            # Save dimensions
            self.boards[self.current_board]['lists'][list_name]['cards'][idx]['width'] = new_width
            self.boards[self.current_board]['lists'][list_name]['cards'][idx]['height'] = new_height
            
            self.save_data()
            self.render_list_cards(list_name)
            
            # Unbind resize events
            self.root.unbind("<B1-Motion>")
            self.root.unbind("<ButtonRelease-1>")
            
            # Re-bind drag events
            self.root.bind("<B1-Motion>", self.on_drag_motion)
            self.root.bind("<ButtonRelease-1>", self.on_drop)
            
            del self.resize_data

# Run the application

if __name__ == "__main__":
    root = ctk.CTk()
    app = TaskBoard(root)
    root.mainloop()
                
