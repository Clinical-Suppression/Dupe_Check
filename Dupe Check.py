import os
import tkinter as tk
from tkinter import filedialog, messagebox, Menu

# Attempt to load Drag and Drop, but don't crash if the OS rejects it
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except (ImportError, RuntimeError):
    DND_AVAILABLE = False

class DuplicateRemoverApp:
    def __init__(self, root, dnd_enabled):
        self.root = root
        self.root.title("Duplicate Line Checker")
        self.root.geometry("850x650")

        # Top Control Panel
        control_frame = tk.Frame(self.root, padx=10, pady=10)
        control_frame.pack(fill=tk.X)

        self.btn_open = tk.Button(control_frame, text="Open File", command=self.open_file_dialog)
        self.btn_open.pack(side=tk.LEFT, padx=5)

        self.btn_skip = tk.Button(control_frame, text="Skip (Keep)", 
                                  command=self.skip_current, state=tk.DISABLED, 
                                  bg="#e0e0e0")
        self.btn_skip.pack(side=tk.LEFT, padx=5)

        self.btn_delete = tk.Button(control_frame, text="Delete Current", 
                                    command=self.delete_current, state=tk.DISABLED, 
                                    bg="#ffcccc", activebackground="#ff9999")
        self.btn_delete.pack(side=tk.LEFT, padx=5)

        self.btn_save = tk.Button(control_frame, text="Save File", command=self.save_file, state=tk.DISABLED)
        self.btn_save.pack(side=tk.LEFT, padx=5)
        
        status_text = "Drag & Drop ready" if dnd_enabled else "DND library missing. Use 'Open File'."
        self.lbl_status = tk.Label(control_frame, text=status_text, fg="gray")
        self.lbl_status.pack(side=tk.RIGHT, padx=5)

        # Text Area with Scrollbars
        text_frame = tk.Frame(self.root)
        text_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        y_scroll = tk.Scrollbar(text_frame)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        x_scroll = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.text_area = tk.Text(text_frame, wrap=tk.NONE, 
                                 yscrollcommand=y_scroll.set, 
                                 xscrollcommand=x_scroll.set,
                                 undo=True)
        self.text_area.pack(expand=True, fill=tk.BOTH)
        
        y_scroll.config(command=self.text_area.yview)
        x_scroll.config(command=self.text_area.xview)

        # Configure highlighting tags
        self.text_area.tag_config("duplicate", background="#ffffb3", foreground="black") # Light Yellow
        self.text_area.tag_config("related_group", background="#b3e5fc", foreground="black") # Light Blue
        self.text_area.tag_config("current_duplicate", background="#ffb300", foreground="black") # Orange
        
        # Configure the standard text selection highlight to stand out and override everything else
        self.text_area.tag_config(tk.SEL, background="#0056b3", foreground="white") 

        # State Variables
        self.current_dup_idx = 0
        self.dup_items = []
        self.known_duplicate_texts = set()

        # Context Menu & Mouse Bindings
        self.context_menu = Menu(self.root, tearoff=0)
        self.text_area.bind("<Button-3>", self.show_context_menu) # Windows/Linux Right Click
        self.text_area.bind("<Button-2>", self.show_context_menu) # Mac Right Click
        self.text_area.bind("<ButtonRelease-1>", self.on_click_text) # Left Click for highlighting
        
        # Keyboard shortcut bindings to trigger rescans when editing (maintaining current index)
        self.text_area.bind("<<Cut>>", lambda e: self.root.after(50, lambda: self.scan_for_duplicates(keep_index=True)))
        self.text_area.bind("<<Paste>>", lambda e: self.root.after(50, lambda: self.scan_for_duplicates(keep_index=True)))
        
        if dnd_enabled:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.handle_drop)
            self.text_area.drop_target_register(DND_FILES)
            self.text_area.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        filepath = event.data
        if filepath.startswith('{') and filepath.endswith('}'):
            filepath = filepath[1:-1]
        elif ' {' in filepath: 
            filepath = filepath.split(' {')[0].strip('{}')
            
        if os.path.isfile(filepath):
            self.load_file(filepath)

    def open_file_dialog(self):
        filepath = filedialog.askopenfilename(
            title="Select a text file",
            filetypes=(("All Files", "*.*"), ("Text Files", "*.txt"), ("CSV Files", "*.csv"))
        )
        if filepath:
            self.load_file(filepath)

    def load_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", content)
            self.scan_for_duplicates(keep_index=False)
            self.btn_save.config(state=tk.NORMAL)
            self.root.title(f"Duplicate Line Checker - {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file:\n{str(e)}")

    def scan_for_duplicates(self, keep_index=False):
        # Save old index if we are pasting text so we don't skip back to 0
        old_idx = self.current_dup_idx if keep_index else 0

        # Clear all dynamically generated tags
        for tag in self.text_area.tag_names():
            if tag.startswith("dup_item_") or tag in ("duplicate", "current_duplicate", "related_group"):
                self.text_area.tag_remove(tag, "1.0", tk.END)

        self.dup_items = []
        self.known_duplicate_texts = set()
        seen = set()

        raw_text = self.text_area.get("1.0", "end-1c")
        lines = raw_text.split('\n')

        counter = 0
        for i, line in enumerate(lines):
            if not line.strip():
                continue

            if line in seen:
                start_idx = f"{i+1}.0"
                end_idx = f"{i+2}.0" 
                
                tag_name = f"dup_item_{counter}"
                
                self.text_area.tag_add("duplicate", start_idx, end_idx)
                self.text_area.tag_add(tag_name, start_idx, end_idx)
                
                self.dup_items.append({"tag": tag_name, "text": line})
                self.known_duplicate_texts.add(line)
                counter += 1
            else:
                seen.add(line)

        # Enforce visual priority (SEL text highlight > Orange > Blue > Yellow)
        self.text_area.tag_raise("duplicate")
        self.text_area.tag_raise("related_group")
        self.text_area.tag_raise("current_duplicate")
        self.text_area.tag_raise(tk.SEL)

        if keep_index and self.dup_items:
            # Ensure we don't go out of bounds if pastes/deletions removed duplicates
            self.current_dup_idx = min(old_idx, len(self.dup_items) - 1)
        else:
            self.current_dup_idx = 0

        self.update_view()

    def update_view(self):
        self.text_area.tag_remove("current_duplicate", "1.0", tk.END)
        self.text_area.tag_remove("related_group", "1.0", tk.END)
        
        valid_dups = []
        for item in self.dup_items:
            if self.text_area.tag_ranges(item["tag"]):
                valid_dups.append(item)
        self.dup_items = valid_dups

        num_duplicates = len(self.dup_items)

        if num_duplicates == 0:
            self.btn_skip.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)
            self.lbl_status.config(text="No duplicates remaining.")
            return

        self.btn_skip.config(state=tk.NORMAL)
        self.btn_delete.config(state=tk.NORMAL)

        if self.current_dup_idx >= num_duplicates:
            self.current_dup_idx = 0

        active_item = self.dup_items[self.current_dup_idx]
        ranges = self.text_area.tag_ranges(active_item["tag"])
        
        if ranges:
            start_idx, end_idx = ranges[0], ranges[1]
            self.text_area.tag_add("current_duplicate", start_idx, end_idx)
            self.text_area.see(start_idx)
            self.highlight_related_lines(active_item["text"])
            
        self.lbl_status.config(text=f"Selected {self.current_dup_idx + 1} of {num_duplicates} duplicates")
        
        # Guarantee selection remains visible on top of newly drawn colors
        self.text_area.tag_raise(tk.SEL)

    def highlight_related_lines(self, text_to_match):
        self.text_area.tag_remove("related_group", "1.0", tk.END)
        if not text_to_match: 
            return
            
        raw_text = self.text_area.get("1.0", "end-1c")
        lines = raw_text.split('\n')
        
        for i, line in enumerate(lines):
            if line == text_to_match:
                self.text_area.tag_add("related_group", f"{i+1}.0", f"{i+2}.0")
                
        # Re-assert priorities after highlighting
        self.text_area.tag_raise("current_duplicate")
        self.text_area.tag_raise(tk.SEL)

    def on_click_text(self, event):
        click_index = self.text_area.index(f"@{event.x},{event.y}")
        line_num = click_index.split('.')[0]
        line_text = self.text_area.get(f"{line_num}.0", f"{line_num}.end")
        
        if line_text in self.known_duplicate_texts:
            self.highlight_related_lines(line_text)
        else:
            self.text_area.tag_remove("related_group", "1.0", tk.END)

    def skip_current(self):
        self.current_dup_idx += 1
        self.update_view()

    def delete_current(self):
        if not self.dup_items: return
        active_item = self.dup_items[self.current_dup_idx]
        ranges = self.text_area.tag_ranges(active_item["tag"])
        
        if ranges:
            self.text_area.delete(ranges[0], ranges[1])
        self.update_view()

    def show_context_menu(self, event):
        click_index = self.text_area.index(f"@{event.x},{event.y}")
        tags = self.text_area.tag_names(click_index)
        target_tag = None
        
        for t in tags:
            if t.startswith("dup_item_"):
                target_tag = t
                break
                
        self.context_menu.delete(0, tk.END)
        
        if target_tag:
            ranges = self.text_area.tag_ranges(target_tag)
            if ranges:
                start, end = ranges[0], ranges[1]
                self.context_menu.add_command(label="Delete this line", 
                                              command=lambda: self.menu_delete_duplicate(target_tag, start, end))
                self.context_menu.add_command(label="Ignore (Keep it and unhighlight)", 
                                              command=lambda: self.menu_ignore_duplicate(target_tag, start, end))
                self.context_menu.add_separator()
        
        self.context_menu.add_command(label="Cut", command=self.menu_cut)
        self.context_menu.add_command(label="Copy", command=self.menu_copy)
        self.context_menu.add_command(label="Paste", command=self.menu_paste)
        
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def menu_delete_duplicate(self, tag, start_idx, end_idx):
        self.text_area.delete(start_idx, end_idx)
        idx = next((i for i, item in enumerate(self.dup_items) if item["tag"] == tag), -1)
        if idx != -1 and idx < self.current_dup_idx:
            self.current_dup_idx -= 1
        self.update_view()

    def menu_ignore_duplicate(self, tag, start_idx, end_idx):
        self.text_area.tag_remove("duplicate", start_idx, end_idx)
        self.text_area.tag_remove(tag, start_idx, end_idx)
        
        idx = next((i for i, item in enumerate(self.dup_items) if item["tag"] == tag), -1)
        if idx != -1 and idx < self.current_dup_idx:
            self.current_dup_idx -= 1
        self.update_view()

    def menu_copy(self):
        try:
            selected_text = self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass 

    def menu_cut(self):
        try:
            selected_text = self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
            self.text_area.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.scan_for_duplicates(keep_index=True)
        except tk.TclError:
            pass

    def menu_paste(self):
        try:
            clipboard_text = self.root.clipboard_get()
            try:
                self.text_area.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
            
            self.text_area.insert(tk.INSERT, clipboard_text)
            self.scan_for_duplicates(keep_index=True) 
        except tk.TclError:
            pass 

    def save_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        if not filepath:
            return
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                content = self.text_area.get("1.0", "end-1c")
                f.write(content)
            messagebox.showinfo("Success", "File saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{str(e)}")

if __name__ == "__main__":
    root = None
    dnd_working = False
    
    if DND_AVAILABLE:
        try:
            root = TkinterDnD.Tk()
            dnd_working = True
        except Exception:
            pass
            
    if not root:
        root = tk.Tk()
        
    app = DuplicateRemoverApp(root, dnd_enabled=dnd_working)
    root.mainloop()