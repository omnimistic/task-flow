# Task Flow

A free and open-source (FOSS) alternative to Trello that runs entirely on your local device. Manage tasks, boards, and workflows offline with a modern desktop interface. Currently under active development.

## Features

- Intuitive drag-and-drop interface for organizing tasks into boards and lists.
- Local data storage using JSON for persistence without external dependencies.
- Customizable dark theme with support for high-quality fonts.
- Dynamic scrollable views for handling large boards.
- Built with Python and CustomTkinter for cross-platform compatibility.

## Prerequisites

- Python 3.8 or higher
- pip for package installation

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/omnimistic/task-flow.git
   cd task-flow
   ```

2. Install required dependencies:
   ```
   pip install customtkinter pyglet
   ```

3. Run the application:
   ```
   python taskflow.py
   ```

The app will launch a desktop window. Ensure the `font` directory is present if using custom fonts.

## Usage

1. Launch the app to see the main dashboard.
2. Create new boards via the sidebar menu.
3. Add lists and cards by clicking the "+" buttons.
4. Drag items to reorder or move between lists.
5. Data saves automatically to local JSON files in the app directory.

For detailed controls, refer to the in-app tooltips.

## Screenshots

### Main Dashboard
![Dashboard](for_readme/dashboard.png)

### Board View with Lists
![Board View](for_readme/board-view.png)

### Task Card Editing
![Card Edit](for_readme/card-edit.png)

## Demo

Quick animation of creating a board and adding tasks:

![Demo GIF](for_readme/demo.gif)

## Architecture

- **GUI Framework**: CustomTkinter for modern, native-like widgets.
- **Core Libraries**: Tkinter for canvas and scrolling, Pyglet for font management, JSON for data serialization.
- **Data Flow**: Local file-based storage with dynamic UI updates.

## Contributing

As the project is in early development, contributions are highly encouraged:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/new-board-layout`).
3. Commit changes (`git commit -m "Add board layout improvements"`).
4. Push to the branch (`git push origin feature/new-board-layout`).
5. Open a Pull Request.

Please discuss major changes via issues first.

See the issues tab for planned features and bugs.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details (add one if not present).

## Acknowledgments

- Built with CustomTkinter for the UI.
- Custom Inter font for typography.
- Inspired by Trello's workflow simplicity.

---

Under development by [omnimistic](https://github.com/omnimistic). Report issues or suggest features!
