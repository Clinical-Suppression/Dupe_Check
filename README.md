# Duplicate Line Checker (`Dupe Check.py`)

A Python desktop application built to help you easily identify, review, and manage duplicate lines in text and CSV files. The script provides an interactive GUI to visually step through duplicates rather than automatically deleting them, giving you full control over your data.

## Features

* **Visual Navigation:** Use the interface to jump between duplicates with "Skip (Keep)" and "Delete Current" controls.


* **Drag-and-Drop Support:** Drag files directly into the window to load them instantly (requires `tkinterdnd2`).


* **Dynamic Color Highlighting:** Easily distinguish between currently selected duplicates, unreviewed duplicates, and their matching pairs.


* **Live Rescanning:** The application automatically updates duplicate tags when you cut, paste, or manually edit the text.


* **Context Menu:** Right-click inside the text area to delete lines, ignore specific duplicates, or perform standard cut/copy/paste actions.



## Requirements

* **Python 3.x**
* **`tkinter`**: Included in the standard Python library.


* **`tkinterdnd2` (Optional)**: Required for drag-and-drop functionality. The app will still function normally using the "Open File" dialog if this library is missing.



To install the optional drag-and-drop library, run:

```bash
pip install tkinterdnd2

```

## Usage

1. Run the script from your terminal:
```bash
python "Dupe Check.py"

```


2. Click **Open File** to select a `.txt` or `.csv` file, or drag and drop a file into the application window.


3. The app will immediately scan and highlight all duplicate lines.


4. Use the **Delete Current** button to remove the currently selected duplicate, or **Skip (Keep)** to leave it and move to the next one.


5. Click **Save File** when you are finished to export your cleaned text.



## Highlighting Color Guide

The application uses specific background colors to help you visualize file contents:

* **Orange:** The currently active duplicate you are reviewing.


* **Light Yellow:** All other identified duplicate lines in the document.


* **Light Blue:** Related lines. Clicking or left-clicking on a highlighted duplicate will color the original matching line(s) in light blue so you can see the context.


* **Dark Blue:** Standard text selection.
