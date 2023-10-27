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
        
        # Frame for directory selection and exit button
        self.directory_frame = ttk.Frame(self.tree_frame)
        self.directory_frame.pack(fill="x")
        
        # Exit button
        self.exit_button = ttk.Button(self.directory_frame, text="Exit", command=self.quit)
        self.exit_button.pack(side="left")
        
        # Entry for manual directory input
        self.directory_var = tk.StringVar()
        self.directory_entry = tk.Entry(self.directory_frame, textvariable=self.directory_var, fg='grey')
        self.directory_entry.insert(0, "change/to/this/directory")
        self.directory_entry.bind("<FocusIn>", self.clear_placeholder)
        self.directory_entry.pack(side="left", fill="x", expand=True)

        
        # Button to select directory
        self.select_directory_button = ttk.Button(self.directory_frame, text="Select Directory", command=self.change_directory)
        self.select_directory_button.pack()

##### FILE TREE #####

    #Build file tree box
    def build_file_tree(self, directory):
        self.file_tree_text.config(state="normal")
        self.file_tree_text.delete(1.0, "end")
        self.generate_file_tree(directory)
        self.file_tree_text.config(state="disabled")

    def generate_file_tree(self, directory, prefix=""):
        tree_str = ""
        line_num = 1
        for path in sorted(directory.iterdir()):
            if path.is_dir():
                dir_line = prefix + "├── " + path.name + "\n"
                self.file_tree_text.insert("end", dir_line, "dir")
                start = f"{line_num}.{len(prefix) + 4}"
                end = f"{line_num}.{len(prefix) + 4 + len(path.name)}"
                self.file_tree_text.tag_add("dir", start, end)
                line_num += 1
                if path in self.expanded_dirs:
                    added_lines = self.generate_file_tree(path, prefix + "│   ")
                    line_num += added_lines
            else:
                file_line = prefix + "├── " + path.name + "\n"
                self.file_tree_text.insert("end", file_line, "file")
                start = f"{line_num}.{len(prefix) + 4}"
                end = f"{line_num}.{len(prefix) + 4 + len(path.name)}"
                self.file_tree_text.tag_add("file", start, end)
                line_num += 1

        return line_num - 1
    
    # code that executes after clicking a directory
    def on_dir_click(self, event):
        # Get the index of the text widget where the click occurred
        index = self.file_tree_text.index("@%d,%d" % (event.x, event.y))
        # Get the line of text at the click index
        line = self.file_tree_text.get("%s linestart" % index, "%s lineend" % index)
        
        # Extract the directory name from the line of text
        dir_name = line.split('├── ')[-1].strip()
        if not dir_name:
            # If the line is not a valid directory name, return early
            #print("Clicked line is not a directory")
            return
        #print("Clicked on:", dir_name)
        # Construct the full path to the clicked directory
        clicked_dir = self.construct_full_path(dir_name, index)
        #print("Full path:", clicked_dir)
        if clicked_dir.is_dir():
            if clicked_dir in self.expanded_dirs:
                self.expanded_dirs.remove(clicked_dir)
            else:
                self.expanded_dirs.add(clicked_dir)
            self.build_file_tree(self.current_directory)
        #else:
            #print("Clicked path is not a directory on the filesystem")

    #reconstructs the path to a clicked on directory to allow nesting
    def construct_full_path(self, dir_name, index):
        constructed_path = Path(dir_name)
        #print("Starting reconstruction with:", constructed_path)

        line_num, col_num = map(int, index.split('.'))
        indent_level = self.get_indent_level(self.file_tree_text.get(index + " linestart", index + " lineend"))
        
        while line_num > 0:
            line_num -= 1
            index = f"{line_num}.0"
            line = self.file_tree_text.get(f"{index} linestart", f"{index} lineend")
            line_indent_level = self.get_indent_level(line)
            
            if line_indent_level < indent_level:
                parent_name = line.split('├── ')[-1].strip()
                constructed_path = Path(parent_name) / constructed_path
                #print("Parent dir updated to:", constructed_path)
                indent_level = line_indent_level

        full_path = self.current_directory / constructed_path
        #print("Constructed full path:", full_path)
        return full_path


    #finds how far indendet a file or directory is so that it can be found
    def get_indent_level(self, line):
        return len(line) - len(line.lstrip('│   '))


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

    #empties the change directory text box as soon as clicked
    def clear_placeholder(self, event):
        if self.directory_entry.get() == "change/to/this/directory":
            self.directory_entry.delete(0, "end")
            self.directory_entry.config(fg='black')

    #uses the change directory button to change to whatever directory was typed into the box
    def change_directory(self):
        directory = self.directory_var.get()
        if directory:
            path = Path(directory)
            if path.exists() and path.is_dir():
                self.current_directory = path
                self.expanded_dirs = set()
                self.build_file_tree(self.current_directory)
            else:
                messagebox.showerror("Error", "Directory not found or not a directory.")
  
  ### SEARCHING ###
  
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

