import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import sv_ttk
import os
from modules.search import index_files, search_files
from typing import Optional, List
from model.File import File
from model.Score import Score

class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Context Builder")
        sv_ttk.set_theme("dark")
        self.source_dir: str = ''
        self.excluded_dirs: List[str] = ['target', 'pyenv', 'node_modules', 'venv', '.idea', '.git', '.vscode', '__pycache__']
        self.indexed_files: List[File] = []
        self.selected_files: List[File] = []
        self.search_results: List[File] = []
        self.results_list_items: List[File] = []
        self.selected_files_items: List[File] = [] 

        self.create_widgets()
        self.bind_shortcuts()

    def create_widgets(self):
        # Frame for directory selection
        dir_frame = ttk.Frame(self.root)
        dir_frame.pack(pady=10, padx=10, fill='x')

        self.dir_label = ttk.Label(dir_frame, text="Source Directory: Not selected")
        self.dir_label.pack(side='left')

        self.dir_button = ttk.Button(dir_frame, text="Open Directory (Ctrl+O)", command=self.open_directory)
        self.dir_button.pack(side='right')

        # Excluded directories
        exclude_frame = ttk.Frame(self.root)
        exclude_frame.pack(pady=5, padx=10, fill='x')

        self.excluded_dirs_label = ttk.Label(exclude_frame, text="Excluded Files/Directories:")
        self.excluded_dirs_label.pack(side='left')
        self.exclude_entry = ttk.Entry(exclude_frame)
        self.exclude_entry.pack(side='left', fill='x', expand=True)
        self.exclude_entry.insert(0, ','.join(self.excluded_dirs))

        # Search field
        search_frame = ttk.Frame(self.root)
        search_frame.pack(pady=5, padx=10, fill='x')

        ttk.Label(search_frame, text="Search:").pack(side='left')
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side='left', fill='x', expand=True)
        self.search_entry.bind('<KeyRelease>', self.on_search)
        self.search_entry.bind('<Return>', self.add_best_match)

        # Results list
        results_frame = ttk.Frame(self.root)
        results_frame.pack(pady=5, padx=10, fill='both', expand=True)

        results_label = ttk.Label(results_frame, text="Search Results")
        results_label.pack()

        self.results_list = tk.Listbox(results_frame, selectmode='extended')
        self.results_list.pack(fill='both', expand=True)
        self.results_list.bind('<Double-Button-1>', self.add_selected_files)

        # Buttons for adding and clearing selection
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=5, padx=10, fill='x')

        self.add_selected_button = ttk.Button(button_frame, text="Add Selected (Ctrl+A)", command=self.add_selected_files)
        self.add_selected_button.pack(side='left')

        self.clear_selection_button = ttk.Button(button_frame, text="Clear Selection (Ctrl+L)", command=self.clear_selection)
        self.clear_selection_button.pack(side='left')

        self.reindex_button = ttk.Button(button_frame, text="Reindex Files (Ctrl+R)", command=self.update_indexed_files)
        self.reindex_button.pack(side='left')

        # Selected files list
        selected_frame = ttk.Frame(self.root)
        selected_frame.pack(pady=5, padx=10, fill='both', expand=True)

        selected_label = ttk.Label(selected_frame, text="Selected Files")
        selected_label.pack()

        self.selected_files_list = tk.Listbox(selected_frame)
        self.selected_files_list.pack(fill='both', expand=True)

        # Preview pane
        preview_frame = ttk.LabelFrame(self.root, text="Preview")
        preview_frame.pack(pady=5, padx=10, fill='both', expand=True)

        self.preview_text = tk.Text(preview_frame, wrap='none', height=10)
        self.preview_text.pack(fill='both', expand=True)
        self.preview_text.config(state='disabled')

        # Buttons
        bottom_button_frame = ttk.Frame(self.root)
        bottom_button_frame.pack(pady=5, padx=10, fill='x')

        self.copy_button = ttk.Button(bottom_button_frame, text="Copy to Clipboard (Ctrl+C)", command=self.copy_to_clipboard)
        self.copy_button.pack(side='right')

        self.remove_selected_button = ttk.Button(button_frame, text="Remove Selected (Del)", command=self.remove_selected_files)
        self.remove_selected_button.pack(side='left')

    def bind_shortcuts(self):
        self.root.bind('<Control-c>', lambda e: self.copy_to_clipboard())
        self.root.bind('<Control-a>', lambda e: self.add_selected_files())
        self.root.bind('<Control-l>', lambda e: self.clear_selection())
        self.root.bind('<Control-r>', lambda e: self.update_indexed_files())
        self.root.bind('<Return>', lambda e: self.add_best_match())
        self.root.bind('<Control-Shift-A>', lambda e: self.select_all())
        self.root.bind('<Control-o>', lambda e: self.open_directory())
        self.root.bind('<Delete>', lambda e: self.remove_selected_files())
        self.selected_files_list.bind('<Double-Button-1>', self.remove_selected_files)

    def open_directory(self):
        dir_name: str = filedialog.askdirectory()
        if dir_name:
            self.source_dir = dir_name
            self.dir_label.config(text=f"Source Directory: {self.source_dir}")
            self.update_indexed_files()

    def update_indexed_files(self):
        excluded_dirs_str: str = self.exclude_entry.get()
        self.excluded_dirs = [d.strip() for d in excluded_dirs_str.split(',') if d.strip()]
        self.indexed_files = index_files(self.source_dir, self.excluded_dirs)
        self.on_search()

    def on_search(self, event: Optional[tk.Event] = None):
        query: str = self.search_entry.get()
        if query:
            self.search_results = search_files(query, self.indexed_files)
        else:
            self.search_results = self.indexed_files
            for file in self.search_results:
                file.score = Score(100, 100, 100)
                file.score.weight_and_calculate()

        # Update the results list with relative paths and directory markings
        self.results_list.delete(0, tk.END)
        self.results_list_items.clear()
        for file in self.search_results:
            rel_path = os.path.relpath(file.path, self.source_dir)
            display_text = f"[DIR] {rel_path}" if file.is_dir else rel_path
            self.results_list.insert(tk.END, display_text)
            self.results_list_items.append(file)

    def add_selected_files(self, event: Optional[tk.Event] = None):
        selected_indices = self.results_list.curselection()
        if not selected_indices and event and event.type == '2':
            clicked_index = self.results_list.nearest(event.y)
            self.results_list.selection_set(clicked_index)
            selected_indices = self.results_list.curselection()

        for index in selected_indices:
            selected_file = self.results_list_items[index]
            if selected_file in self.selected_files:
                continue
            if selected_file.is_dir:
                # Add directory
                self.selected_files.append(selected_file)
                rel_path = os.path.relpath(selected_file.path, self.source_dir)
                display_text = f"[DIR] {rel_path}"
                self.selected_files_list.insert(tk.END, display_text)
                self.selected_files_items.append(selected_file)
                # Add all files in directory
                self.add_files_from_directory(selected_file)
            else:
                self.selected_files.append(selected_file)
                rel_path = os.path.relpath(selected_file.path, self.source_dir)
                display_text = rel_path
                self.selected_files_list.insert(tk.END, display_text)
                self.selected_files_items.append(selected_file)
        self.update_preview()
        self.results_list.selection_clear(0, tk.END)

    def add_files_from_directory(self, directory_file: File):
        dir_path = directory_file.path
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                if any(f.path == file_path for f in self.selected_files):
                    continue
                file_obj = next((f for f in self.indexed_files if f.path == file_path), None)
                if file_obj:
                    self.selected_files.append(file_obj)
                    rel_path = os.path.relpath(file_obj.path, self.source_dir)
                    display_text = '    ' + rel_path  # Indent to show hierarchy
                    self.selected_files_list.insert(tk.END, display_text)
                    self.selected_files_items.append(file_obj)

    def add_best_match(self, event: Optional[tk.Event] = None):
        selected_indices = self.results_list.curselection()
        if selected_indices:
            self.add_selected_files()
        else:
            if self.search_results:
                best_match = self.search_results[0]
                if best_match not in self.selected_files:
                    self.selected_files.append(best_match)
                    rel_path = os.path.relpath(best_match.path, self.source_dir)
                    display_text = f"[DIR] {rel_path}" if best_match.is_dir else rel_path
                    self.selected_files_list.insert(tk.END, display_text)
                    self.selected_files_items.append(best_match)
                    if best_match.is_dir:
                        self.add_files_from_directory(best_match)
                    self.update_preview()

    def clear_selection(self):
        self.selected_files.clear()
        self.selected_files_items.clear()
        self.selected_files_list.delete(0, tk.END)
        self.update_preview()
        self.results_list.selection_clear(0, tk.END)

    def copy_to_clipboard(self):
        if not self.selected_files:
            messagebox.showwarning("No Selection", "No files selected.")
            return
        # Prepare the content to copy
        content_pieces: list[str] = []
        for file in self.selected_files:
            if file.is_dir:
                continue  # Skip directories in clipboard content
            content_pieces.append(f"==== {os.path.relpath(file.path, self.source_dir)} ====\n\n{file.content}\n")
        content = '\n'.join(content_pieces)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Copied", "Selected files copied to clipboard.")

    def update_preview(self):
        if not self.selected_files:
            self.preview_text.config(state='normal')
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.config(state='disabled')
            return
        # Prepare the content to display
        content_pieces: list[str] = []
        for file in self.selected_files:
            if file.is_dir:
                continue  # Skip directories in preview
            content_pieces.append(f"==== {os.path.relpath(file.path, self.source_dir)} ====\n\n{file.content}\n")
        content = '\n'.join(content_pieces)
        self.preview_text.config(state='normal')
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, content)
        self.preview_text.config(state='disabled')

    def remove_selected_files(self, event: Optional[tk.Event] = None):
        selected_indices = self.selected_files_list.curselection()
        if not selected_indices and event and event.type == '2':
            clicked_index = self.selected_files_list.nearest(event.y)
            self.selected_files_list.selection_set(clicked_index)
            selected_indices = self.selected_files_list.curselection()

        indices_to_remove = sorted(selected_indices, reverse=True)
        for index in indices_to_remove:
            file_to_remove = self.selected_files_items[index]
            if file_to_remove.is_dir:
                dir_path = file_to_remove.path
                self.selected_files.pop(index)
                self.selected_files_items.pop(index)
                self.selected_files_list.delete(index)
                # Remove all files under this directory
                indices_to_remove_sub = []
                for i in range(len(self.selected_files)):
                    f = self.selected_files[i]
                    if f.path.startswith(dir_path):
                        indices_to_remove_sub.append(i)
                for i in sorted(indices_to_remove_sub, reverse=True):
                    self.selected_files.pop(i)
                    self.selected_files_items.pop(i)
                    self.selected_files_list.delete(i)
            else:
                self.selected_files.pop(index)
                self.selected_files_items.pop(index)
                self.selected_files_list.delete(index)
        self.update_preview()
        self.selected_files_list.selection_clear(0, tk.END)