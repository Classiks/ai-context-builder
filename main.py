import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import sv_ttk
import os
from search import index_files, search_files
from typing import Optional

class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Context Builder")
        sv_ttk.set_theme("dark")
        self.source_dir: str = ''
        self.excluded_dirs: list[str] = ['target', 'pyenv', 'node_modules']
        self.indexed_files: list[tuple[str, str]] = []
        self.selected_files: list[str] = []
        self.search_results: list[tuple[str, str, int]] = []  # List of tuples (file_path, content, score)

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

        ttk.Label(exclude_frame, text="Excluded Subdirectories (comma-separated):").pack(side='left')
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

    def bind_shortcuts(self):
        self.root.bind('<Control-c>', lambda e: self.copy_to_clipboard())
        self.root.bind('<Control-a>', lambda e: self.add_selected_files())
        self.root.bind('<Control-l>', lambda e: self.clear_selection())
        self.root.bind('<Control-r>', lambda e: self.update_indexed_files())
        self.root.bind('<Return>', lambda e: self.add_best_match())
        self.root.bind('<Control-Shift-A>', lambda e: self.select_all())
        self.root.bind('<Control-o>', lambda e: self.open_directory())

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
            self.search_results = search_files(self.indexed_files, query)
        else:
            self.search_results = [(path, content, 100) for path, content in self.indexed_files]
        self.results_list.delete(0, tk.END)
        for file_path, _, score in self.search_results:
            self.results_list.insert(tk.END, file_path)

    def add_selected_files(self, event: Optional[tk.Event] = None):
        selected_indices = self.results_list.curselection()
        if not selected_indices and event and event.type == '2':  # If double-clicked but no selection
            # Select the clicked item
            clicked_index = self.results_list.nearest(event.y)
            self.results_list.selection_set(clicked_index)
            selected_indices = self.results_list.curselection()

        for index in selected_indices:
            file_path = self.results_list.get(index)
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
                self.selected_files_list.insert(tk.END, file_path)
        self.update_preview()
        # Clear selection in results list
        self.results_list.selection_clear(0, tk.END)

    def add_best_match(self, event: Optional[tk.Event] = None):
        # Check if any files are selected
        selected_indices = self.results_list.curselection()
        
        if selected_indices:
            # If files are selected, add those files
            self.add_selected_files()
        else:
            # If no files are selected, add the best match
            if self.search_results:
                best_match = self.search_results[0][0]  # Get file_path of the best match
                if best_match not in self.selected_files:
                    self.selected_files.append(best_match)
                    self.selected_files_list.insert(tk.END, best_match)
                self.update_preview()

    def clear_selection(self):
        self.selected_files.clear()
        self.selected_files_list.delete(0, tk.END)
        self.update_preview()
        # Clear selection in results list
        self.results_list.selection_clear(0, tk.END)

    def copy_to_clipboard(self):
        if not self.selected_files:
            messagebox.showwarning("No Selection", "No files selected.")
            return
        # Prepare the content to copy
        content_pieces: list[str] = []
        for file_path in self.selected_files:
            file_content = self.get_file_content(file_path)
            if file_content is not None:
                content_pieces.append(f"==== {os.path.relpath(file_path, self.source_dir)} ====\n\n{file_content}\n")
        content = '\n'.join(content_pieces)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Copied", "Selected files copied to clipboard.")

    def get_file_content(self, file_path: str) -> Optional[str]:
        for path, content in self.indexed_files:
            if path == file_path:
                return content
        return None

    def update_preview(self):
        if not self.selected_files:
            self.preview_text.config(state='normal')
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.config(state='disabled')
            return
        # Prepare the content to display
        content_pieces: list[str] = []
        for file_path in self.selected_files:
            file_content = self.get_file_content(file_path)
            if file_content is not None:
                content_pieces.append(f"==== {os.path.relpath(file_path, self.source_dir)} ====\n\n{file_content}\n")
        content = '\n'.join(content_pieces)
        self.preview_text.config(state='normal')
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, content)
        self.preview_text.config(state='disabled')

    def select_all(self):
        self.selected_files = [file_path for file_path, _, _ in self.search_results]
        self.selected_files_list.delete(0, tk.END)
        for file_path in self.selected_files:
            self.selected_files_list.insert(tk.END, file_path)
        self.update_preview()
        # Clear selection in results list
        self.results_list.selection_clear(0, tk.END)

def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
