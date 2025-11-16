import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime

class TaskBoard:
    def __init__(self, root):
        self.root = root
        self.root.title("TaskFlow - Offline Task Manager")
        self.root.geometry("1200x700")
        self.root.configure(bg="#1e1e2e")
        
        self.data_file = "taskflow_data.json"
        self.boards = {}
        self.current_board = None
        self.drag_data = {"item": None, "source": None, "widget": None, "ghost": None, "last_target": None, "type": None}
        self.list_frames = {}  # Track list frames for drop detection
        self.list_order = {}  # Track order of lists for each board
        
        self.load_data()
        self.setup_ui()
        
        if not self.boards:
            self.create_board("My First Board")
    
    def load_data(self):
        """Load data from JSON file"""
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
        """Save data to JSON file"""
        data = {
            'boards': self.boards,
            'current_board': self.current_board
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def setup_ui(self):
        """Setup the main UI"""
        # Top bar
        top_frame = tk.Frame(self.root, bg="#2d2d44", height=50)
        top_frame.pack(fill=tk.X, side=tk.TOP)
        
        tk.Label(top_frame, text="📋 TaskFlow", font=("Arial", 16, "bold"), 
                bg="#2d2d44", fg="#cdd6f4").pack(side=tk.LEFT, padx=20, pady=10)
        
        # Board selector
        tk.Label(top_frame, text="Board:", bg="#2d2d44", fg="#cdd6f4",
                font=("Arial", 10)).pack(side=tk.LEFT, padx=(50, 5))
        
        self.board_var = tk.StringVar()
        self.board_dropdown = ttk.Combobox(top_frame, textvariable=self.board_var,
                                          state="readonly", width=20)
        self.board_dropdown.pack(side=tk.LEFT, padx=5)
        self.board_dropdown.bind("<<ComboboxSelected>>", self.switch_board)
        
        # Buttons
        btn_style = {"bg": "#89b4fa", "fg": "#1e1e2e", "font": ("Arial", 10, "bold"),
                    "relief": tk.FLAT, "padx": 15, "pady": 5, "cursor": "hand2"}
        
        tk.Button(top_frame, text="+ New Board", command=self.create_board_dialog,
                 **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="+ New List", command=self.create_list_dialog,
                 **btn_style).pack(side=tk.LEFT, padx=5)
        
        # Main canvas with scrollbar
        canvas_frame = tk.Frame(self.root, bg="#1e1e2e")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#1e1e2e", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.lists_frame = tk.Frame(self.canvas, bg="#1e1e2e")
        self.canvas.create_window((0, 0), window=self.lists_frame, anchor="nw")
        
        self.lists_frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        
        self.update_board_list()
        if self.current_board:
            self.render_board()
    
    def update_board_list(self):
        """Update the board dropdown"""
        board_names = list(self.boards.keys())
        self.board_dropdown['values'] = board_names
        if self.current_board in board_names:
            self.board_var.set(self.current_board)
        elif board_names:
            self.board_var.set(board_names[0])
            self.current_board = board_names[0]
    
    def create_board_dialog(self):
        """Create a new board"""
        name = simpledialog.askstring("New Board", "Enter board name:")
        if name:
            self.create_board(name)
    
    def create_board(self, name):
        """Create a new board"""
        if name in self.boards:
            messagebox.showwarning("Warning", "Board already exists!")
            return
        
        self.boards[name] = {"lists": {}}
        self.current_board = name
        self.update_board_list()
        self.render_board()
        self.save_data()
    
    def switch_board(self, event=None):
        """Switch to a different board"""
        self.current_board = self.board_var.get()
        self.render_board()
        self.save_data()
    
    def create_list_dialog(self):
        """Create a new list"""
        if not self.current_board:
            messagebox.showwarning("Warning", "Create a board first!")
            return
        
        name = simpledialog.askstring("New List", "Enter list name:")
        print(f"DEBUG: List name entered: '{name}'")  # Debug
        print(f"DEBUG: Current board: '{self.current_board}'")  # Debug
        if name:
            self.create_list(name)
    
    def create_list(self, name):
        """Create a new list in current board"""
        print(f"DEBUG: create_list called with name: '{name}'")  # Debug
        if not name or name.strip() == "":
            print("DEBUG: Name was empty or None")  # Debug
            return
        
        name = name.strip()
        board = self.boards[self.current_board]
        print(f"DEBUG: Board data before: {board}")  # Debug
        
        if name in board["lists"]:
            messagebox.showwarning("Warning", "List already exists!")
            return
        
        board["lists"][name] = {"cards": []}
        print(f"DEBUG: Board data after: {board}")  # Debug
        self.render_board()
        self.save_data()
        print("DEBUG: List created and saved!")  # Debug
    
    def create_card(self, list_name):
        """Create a new card in a list"""
        title = simpledialog.askstring("New Card", "Enter card title:")
        if title:
            board = self.boards[self.current_board]
            card = {
                "title": title,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            board["lists"][list_name]["cards"].append(card)
            self.render_board()
            self.save_data()
    
    def delete_card(self, list_name, card_index):
        """Delete a card"""
        if messagebox.askyesno("Confirm", "Delete this card?"):
            board = self.boards[self.current_board]
            board["lists"][list_name]["cards"].pop(card_index)
            self.render_board()
            self.save_data()
    
    def delete_list(self, list_name):
        """Delete a list"""
        if messagebox.askyesno("Confirm", f"Delete list '{list_name}' and all its cards?"):
            board = self.boards[self.current_board]
            del board["lists"][list_name]
            self.render_board()
            self.save_data()
    
    def start_drag(self, event, list_name, card_index, widget):
        """Start dragging a card"""
        print(f"DEBUG: start_drag called - list: {list_name}, card: {card_index}")
        self.drag_data["item"] = card_index
        self.drag_data["source"] = list_name
        self.drag_data["widget"] = widget
        
        # Make original card semi-transparent
        widget.configure(relief=tk.SUNKEN, bg="#45475a")
        
        # Create ghost card that follows mouse
        board = self.boards[self.current_board]
        card = board["lists"][list_name]["cards"][card_index]
        
        ghost = tk.Toplevel(self.root)
        ghost.overrideredirect(True)  # Remove window decorations
        ghost.attributes('-alpha', 0.8)  # Semi-transparent
        ghost.attributes('-topmost', True)  # Always on top
        
        ghost_frame = tk.Frame(ghost, bg="#313244", relief=tk.RAISED, bd=2, width=250)
        ghost_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(ghost_frame, text=card["title"], bg="#313244", fg="#cdd6f4",
                font=("Arial", 10, "bold"), wraplength=230, justify=tk.LEFT,
                padx=10, pady=10).pack(fill=tk.X)
        
        # Position ghost at mouse
        ghost.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
        
        self.drag_data["ghost"] = ghost
        print("DEBUG: Ghost created, binding events")
        
        # Bind motion to root window
        self.root.bind("<Motion>", self.drag_motion)
        self.root.bind("<ButtonRelease-1>", self.end_drag)
    
    def drag_motion(self, event):
        """Update ghost card position as mouse moves"""
        if self.drag_data["ghost"]:
            # Update ghost position
            x = event.x_root + 10
            y = event.y_root + 10
            self.drag_data["ghost"].geometry(f"+{x}+{y}")
            
            # Highlight target list
            self.highlight_drop_target(event.x_root, event.y_root)
    
    def highlight_drop_target(self, x, y):
        """Highlight the list that would receive the drop"""
        # Find current target list
        current_target = None
        for list_name, frame in self.list_frames.items():
            fx = frame.winfo_rootx()
            fy = frame.winfo_rooty()
            fw = frame.winfo_width()
            fh = frame.winfo_height()
            
            if fx <= x <= fx + fw and fy <= y <= fy + fh:
                current_target = list_name
                break
        
        # Only update if target changed
        if current_target != self.drag_data.get("last_target"):
            # Reset all list highlights
            for frame in self.list_frames.values():
                frame.configure(relief=tk.RAISED, bd=1)
            
            # Highlight new target
            if current_target:
                self.list_frames[current_target].configure(relief=tk.SOLID, bd=3)
            
            self.drag_data["last_target"] = current_target
    
    def end_drag(self, event):
        """End dragging and find drop target"""
        print(f"DEBUG: end_drag called at position {event.x_root}, {event.y_root}")
        
        # Unbind motion events
        self.root.unbind("<Motion>")
        self.root.unbind("<ButtonRelease-1>")
        
        if self.drag_data["item"] is None:
            print("DEBUG: No item being dragged")
            return
        
        # Destroy ghost card
        if self.drag_data["ghost"]:
            self.drag_data["ghost"].destroy()
        
        # Get mouse position relative to root
        x, y = event.x_root, event.y_root
        
        # Find which list frame the mouse is over
        target_list = None
        for list_name, frame in self.list_frames.items():
            fx = frame.winfo_rootx()
            fy = frame.winfo_rooty()
            fw = frame.winfo_width()
            fh = frame.winfo_height()
            
            print(f"DEBUG: Checking list '{list_name}' - frame at ({fx}, {fy}) size ({fw}x{fh})")
            
            if fx <= x <= fx + fw and fy <= y <= fy + fh:
                target_list = list_name
                print(f"DEBUG: Found target list: {target_list}")
                break
        
        # Move card if valid drop
        if target_list:
            source_list = self.drag_data["source"]
            card_index = self.drag_data["item"]
            
            print(f"DEBUG: Moving card from '{source_list}' to '{target_list}'")
            
            board = self.boards[self.current_board]
            card = board["lists"][source_list]["cards"].pop(card_index)
            board["lists"][target_list]["cards"].append(card)
            
            self.save_data()
        else:
            print("DEBUG: No target list found - card not moved")
        
        # Reset everything
        self.drag_data = {"item": None, "source": None, "widget": None, "ghost": None, "last_target": None}
        self.render_board()
    
    def render_board(self):
        """Render the current board"""
        print(f"DEBUG: render_board called for '{self.current_board}'")  # Debug
        
        # Clear existing widgets
        for widget in self.lists_frame.winfo_children():
            widget.destroy()
        
        self.list_frames = {}  # Reset list frames tracking
        
        if not self.current_board or self.current_board not in self.boards:
            print("DEBUG: No current board or board not found")  # Debug
            return
        
        board = self.boards[self.current_board]
        print(f"DEBUG: Rendering board with {len(board['lists'])} lists")  # Debug
        
        for list_name, list_data in board["lists"].items():
            print(f"DEBUG: Rendering list '{list_name}'")  # Debug
            self.render_list(list_name, list_data)
        
        # Force update
        self.lists_frame.update_idletasks()
        self.canvas.update_idletasks()
    
    def render_list(self, list_name, list_data):
        """Render a single list"""
        list_frame = tk.Frame(self.lists_frame, bg="#2d2d44", width=280, relief=tk.RAISED, bd=1)
        list_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, anchor="n")
        
        # Store reference for drop detection
        self.list_frames[list_name] = list_frame
        
        # List header
        header = tk.Frame(list_frame, bg="#45475a", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text=list_name, bg="#45475a", fg="#cdd6f4",
                font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10, pady=8)
        
        tk.Button(header, text="×", command=lambda: self.delete_list(list_name),
                 bg="#45475a", fg="#f38ba8", font=("Arial", 14, "bold"),
                 relief=tk.FLAT, cursor="hand2").pack(side=tk.RIGHT, padx=5)
        
        # Cards container with scrollbar
        cards_canvas = tk.Canvas(list_frame, bg="#2d2d44", highlightthickness=0, height=400)
        cards_scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=cards_canvas.yview)
        cards_canvas.configure(yscrollcommand=cards_scrollbar.set)
        
        cards_frame = tk.Frame(cards_canvas, bg="#2d2d44")
        cards_canvas.create_window((0, 0), window=cards_frame, anchor="nw", width=260)
        
        cards_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        cards_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        
        # Render cards
        for idx, card in enumerate(list_data["cards"]):
            self.render_card(cards_frame, list_name, idx, card)
        
        cards_frame.bind("<Configure>", lambda e: cards_canvas.configure(
            scrollregion=cards_canvas.bbox("all")))
        
        # Add card button
        tk.Button(list_frame, text="+ Add Card", command=lambda: self.create_card(list_name),
                 bg="#313244", fg="#cdd6f4", relief=tk.FLAT, pady=8,
                 cursor="hand2").pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)
    
    def render_card(self, parent, list_name, card_index, card):
        """Render a single card"""
        card_frame = tk.Frame(parent, bg="#313244", relief=tk.RAISED, bd=1, cursor="hand2")
        card_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Card content
        content_frame = tk.Frame(card_frame, bg="#313244", cursor="hand2")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        
        # Title (draggable area)
        title_label = tk.Label(content_frame, text=card["title"], bg="#313244", fg="#cdd6f4",
                font=("Arial", 10), wraplength=240, justify=tk.LEFT,
                anchor="w", cursor="hand2")
        title_label.pack(fill=tk.X)
        
        # Date
        date_label = tk.Label(content_frame, text=card["created"], bg="#313244", fg="#6c7086",
                font=("Arial", 8), cursor="hand2")
        date_label.pack(anchor="w", pady=(5, 0))
        
        # Delete button (separate frame to prevent drag trigger)
        delete_frame = tk.Frame(content_frame, bg="#313244")
        delete_frame.pack(anchor="e", pady=(5, 0))
        
        delete_btn = tk.Button(delete_frame, text="Delete", 
                 command=lambda: self.delete_card(list_name, card_index),
                 bg="#f38ba8", fg="#1e1e2e", font=("Arial", 8), relief=tk.FLAT,
                 cursor="hand2", padx=8, pady=2)
        delete_btn.pack()
        
        # Bind drag events to all draggable elements EXCEPT delete button
        def start_drag_wrapper(e):
            # Don't start drag if clicking on delete button
            if e.widget == delete_btn or e.widget == delete_frame:
                return
            self.start_drag(e, list_name, card_index, card_frame)
        
        card_frame.bind("<Button-1>", start_drag_wrapper)
        content_frame.bind("<Button-1>", start_drag_wrapper)
        title_label.bind("<Button-1>", start_drag_wrapper)
        date_label.bind("<Button-1>", start_drag_wrapper)

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskBoard(root)
    root.mainloop()