import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import os
from pathlib import Path

from .searcher import ScrollSearch
from .config import *

class TextSearchGUI(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.title("paPYrus Text Search")
        self.geometry("800x600")
        
        self.create_widgets()
        self.current_directory = Path.cwd()
        self.expanded_dirs = set()
        self.searcher = ScrollSearch(str(self.current_directory))
        self.build_file_tree(self.current_directory)

    def create_widgets(self):
        # Frame for the file tree
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(side="left", fill="y")
        
        # Frame for the search bar and results
        self.search_frame = ttk.Frame(self)
        self.search_frame.pack(side="left", fill="both", expand=True)
        
        # Search bar
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<Return>", self.perform_search)  # Bind Enter key to perform search
        
        # Text box for file preview
        self.text = tk.Text(self.search_frame, wrap="word")
        self.text.pack(fill="both", expand=True)
        
        # Button to select directory
        self.select_directory_button = ttk.Button(self.tree_frame, text="Select Directory", command=self.select_directory)
        self.select_directory_button.pack()
        
        # Text widget for file tree
        self.file_tree_text = tk.Text(self.tree_frame, wrap="none", state="disabled", cursor="arrow")
        self.file_tree_text.pack(fill="both", expand=True)
        self.file_tree_text.tag_configure("dir", foreground="blue", underline=True)
        self.file_tree_text.tag_bind("dir", "<Button-1>", self.on_dir_click)

        # Listbox for search results
        self.results_listbox = tk.Listbox(self.search_frame)
        self.results_listbox.pack(fill="both", expand=True)
        self.results_listbox.bind("<<ListboxSelect>>", self.on_result_select)

        # Text box for file preview
        self.file_preview_text = scrolledtext.ScrolledText(self.search_frame, wrap="word")
        self.file_preview_text.pack(fill="both", expand=True)

        #button for clicking to open files
        self.file_tree_text.tag_bind("file", "<Button-1>", self.on_file_click)


    #Build file tree box
    def build_file_tree(self, directory):
        self.file_tree_text.config(state="normal")
        self.file_tree_text.delete(1.0, "end")
        self.file_tree_text.insert("end", self.generate_file_tree(directory))
        self.file_tree_text.config(state="disabled")

    #generate file tree text/ buttons
    def generate_file_tree(self, directory, prefix=""):
        tree_str = ""
        for path in sorted(directory.iterdir()):
            if path.is_dir():
                tree_str += prefix + "├── "
                start = f"{prefix}1.0"
                end = f"{prefix}end"
                self.file_tree_text.insert("end", path.name + "\n", "dir")
                self.file_tree_text.tag_add("dir", start, end)
                if path in self.expanded_dirs:
                    tree_str += self.generate_file_tree(path, prefix + "│   ")
            else:
                tree_str += prefix + "├── " + path.name + "\n"
        return tree_str

    #actions on button clicks for file tree
    def on_dir_click(self, event):
        # Get the index of the text widget where the click occurred
        index = self.file_tree_text.index("@%d,%d" % (event.x, event.y))
        # Get the line of text at the click index
        line = self.file_tree_text.get("%s linestart" % index, "%s lineend" % index)
        # Extract the directory name from the line of text
        dir_name = line.strip("├── \n")
        # Construct the full path to the clicked directory
        clicked_dir = self.current_directory / dir_name
        if clicked_dir.is_dir():
            if clicked_dir in self.expanded_dirs:
                self.expanded_dirs.remove(clicked_dir)
            else:
                self.expanded_dirs.add(clicked_dir)
            self.build_file_tree(self.current_directory)

    #actions for clicking a file in the file tree
    def on_file_click(self, event):
        try:
            # Get the index of the text widget where the click occurred
            index = self.file_tree_text.index("@%d,%d" % (event.x, event.y))
            # Get the line of text at the click index
            line = self.file_tree_text.get("%s linestart" % index, "%s lineend" % index)
            # Extract the file path from the line of text
            file_path = line.strip("├── \n")
            # Construct the full path to the clicked file
            clicked_file = self.current_directory / file_path
            if clicked_file.is_file():
                with clicked_file.open('r') as f:
                    content = f.read()
                self.file_preview_text.delete(1.0, "end")
                self.file_preview_text.insert("end", content)
        except Exception as e:
            print("Error:", str(e))
            tk.messagebox.showerror("Error", f"An error occurred: {str(e)}")



    def select_directory(self):
        directory = filedialog.askdirectory(initialdir=self.current_directory)
        if directory:
            self.current_directory=Path(directory)
            self.expanded_dirs = set()
            self.bild_file_tree(self.current_directory)
  
    def perform_search(self, event):
        query = self.search_var.get()
        results = self.searcher.search(query)  # Perform the search using the ScrollSearch class
        self.display_results(results)

    def display_results(self, results):
        self.results_listbox.delete(0, "end")
        for file, preview in results:
            self.results_listbox.insert("end", file)

    def on_result_select(self, event):
        selected_index = self.results_listbox.curselection()
        if selected_index:
            selected_file = self.results_listbox.get(selected_index)
            content = self.searcher.files[selected_file]
            query = self.search_var.get()
        
            # Use _get_preview to generate a context-aware preview
            preview = self.searcher._get_preview(content, self.searcher.tokenize(query))
            
            self.file_preview_text.delete(1.0, "end")
            self.file_preview_text.insert("end", preview)


def main():
    app = TextSearchGUI()
    app.mainloop()

if __name__ == "__main__":
    main()

