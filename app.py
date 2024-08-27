import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import json
import webbrowser
from threading import Thread
from chat import summarize_document
from preprocessor import Preprocessor

class AsyncChat(Thread):
    def __init__(self, path):
        super().__init__()
        self.path = path
    def run(self):
        self.response = summarize_document(self.path)

class FileSense(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Sense")
        self.geometry("840x1040+50+50")
        self.resizable(False, False)

        # Init variables
        self.current_path = os.getcwd()
        self.var_address = tk.StringVar()
        self.var_address.set(os.getcwd())
        self.var_animation = tk.StringVar()
        self.var_animation.set("░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒")

        # Init frames
        self.labelframe_explorer = tk.LabelFrame(self, text = "Explorer", height = 1000, width = 800)
        self.labelframe_explorer.place(x = 20, y = 20)
        tk.Label(self.labelframe_explorer, textvariable = self.var_address, anchor="w", justify = tk.LEFT).place(x = 20, y = 20)
        self.frame_files = tk.Frame(self.labelframe_explorer, height = 800, width = 760)
        self.frame_files.place(x = 20, y = 60)
        self.display_files(os.getcwd())

        self.frame_senses = tk.Frame(self, height = 1000, width = 800)
        self.frame_senses.place(x = 840, y = 20)
        self.labelframe_preview = tk.LabelFrame(self.frame_senses, text = "Preview", height = 400, width = 800)
        self.labelframe_preview.pack(fill = tk.BOTH, expand = False, pady = 8)
        self.labelframe_summary = tk.LabelFrame(self.frame_senses, text = "Summary", height = 200, width = 800)
        self.labelframe_summary.pack(fill = tk.BOTH, expand = False, pady = 8)
        self.labelframe_sense = tk.LabelFrame(self.frame_senses, text = "Sense", height = 400, width = 800)
        self.labelframe_sense.pack(fill = tk.BOTH, expand = True, pady = 8)

    def display_files(self, path):

        def get_icon(item_path):
            def get_icon_uri():
                if os.path.isdir(item_path):
                    return "./resources/folder.png"
                _, file_extension = os.path.splitext(item_path)
                if file_extension in [".txt", ".pdf", ".xlsx", ".xls", ".doc", ".docx", ".md"]:
                    return "./resources/{}.png".format(file_extension[1:])
                return "./resources/file.png"
            icon = Image.open(get_icon_uri())
            icon = ImageTk.PhotoImage(icon.resize((80, 80)))
            return icon

        def on_item_click(path):
            for widget in self.labelframe_preview.winfo_children():
                widget.destroy()
            for widget in self.labelframe_summary.winfo_children():
                widget.destroy()
            for widget in self.labelframe_sense.winfo_children():
                widget.destroy()
            if os.path.isdir(path):
                self.geometry("840x1040")
                for widget in self.frame_files.winfo_children():
                    widget.destroy()
                self.current_path = os.path.abspath(path)
                self.var_address.set(self.current_path)
                self.display_files(path)
            else:
                self.preview_file(path)
        try:
            items = ["..\\"] + os.listdir(path)
        except PermissionError:
            messagebox.showerror("Error", "You do not have permission to access this folder.")
            on_item_click(os.getcwd())
            return

        truncate_name = lambda name: name if len(name) < 18 else name[:15] + "..."

        for idx, item in enumerate(items):
            item_path = os.path.abspath(os.path.join(path, item))
            icon = get_icon(item_path)
            button = tk.Button(self.frame_files, text = truncate_name(item), image = icon, compound = "top", command = lambda p=item_path: on_item_click(p), height = 100, width = 100, background = "#f0f0f0", borderwidth = 0)
            button.image = icon
            button.grid(row = idx // 6, column = idx % 6, padx = 10, pady = 10)

    def monitor_thread(self, thread):
        if thread.is_alive():
            self.after(200, lambda: self.monitor(thread))
            _animation = self.var_animation.get()
            _animation = _animation[-1] + _animation[:-1]
            self.var_animation.set(_animation)
        else:
            self.update_senses(thread.response)

    def update_senses(self, response):
        payload = json.loads(response)
        summary = payload["summary"]
        actions = payload["actions"]

        for widget in self.labelframe_summary.winfo_children():
            widget.destroy()
        for widget in self.labelframe_sense.winfo_children():
            widget.destroy()

        scrolledtext_summary = scrolledtext.ScrolledText(self.labelframe_summary, height = 12, width = 94, wrap = tk.WORD, background = "#f0f0f0", borderwidth = 0, state = tk.NORMAL)
        scrolledtext_summary.insert(tk.END, summary)
        scrolledtext_summary.configure(state = tk.DISABLED)
        scrolledtext_summary.pack()

        def mailto(mailto_uri):
            webbrowser.open(mailto_uri)
        def not_implemented():
            messagebox.showerror("Warning", "Action not supported yet")

        for idx, action in enumerate(actions):
            _action = action["action"]
            suggest = action["suggest"]

            if _action in ["mail", "todo", "renaming"]:
                action_text = ""
                button_text = ""
                button_command = not_implemented
                if _action == "mail":
                    action_text = "{}. Draft an E-mail with subject \"{}\"".format(idx + 1, suggest.get("title",""))
                    button_text = "Draft"
                    button_command = lambda mailto_uri = "mailto:{to}?subject={subject}&body={body}"\
                        .format(to = suggest.get("to",""), subject = suggest.get("title",""), body = suggest.get("body",""))\
                        .replace(" ","%20")\
                        .replace(",", "%2C") : mailto(mailto_uri)
                elif _action == "todo":
                    action_text = "{}. Create TODO item \"{}\""\
                        .format(idx + 1, suggest.get("title",""))
                    button_text = "Create"
                elif _action == "renaming":
                    action_text = "{}. Rename this file to \"{}\""\
                        .format(idx + 1, suggest)
                    button_text = "Rename"

                _frame = tk.Frame(self.labelframe_sense)
                _frame.pack(fill = tk.BOTH, expand = True, pady = 1)

                tk.Label(_frame, text = action_text, height = 2, anchor="w", justify = tk.LEFT)\
                    .pack(side = tk.LEFT)
                tk.Button(_frame, text = button_text, command = button_command, height = 1, width = 10)\
                    .pack(side = tk.LEFT, padx = 20)

    def preview_file(self, path):
        _, file_extension = os.path.splitext(path)
        if file_extension in [".txt", ".pdf", ".xlsx", ".xls", ".doc", ".docx", ".md"]:
            content = Preprocessor.create(path).process()

            scrolledtext_preview = scrolledtext.ScrolledText(self.labelframe_preview, height = 32, width = 94, wrap = tk.WORD, background = "#f0f0f0", borderwidth = 0, state = tk.NORMAL)
            scrolledtext_preview.insert(tk.END, content)
            scrolledtext_preview.configure(state = tk.DISABLED)
            scrolledtext_preview.pack()

            for widget in self.labelframe_summary.winfo_children():
                widget.destroy()
            for widget in self.labelframe_sense.winfo_children():
                widget.destroy()

            tk.Label(self.labelframe_summary, textvariable = self.var_animation, height = 12).pack(expand = True, fill = tk.BOTH)
            tk.Label(self.labelframe_sense, textvariable = self.var_animation, height = 12).pack(expand = True, fill = tk.BOTH)

            chat_thread = AsyncChat(path)
            chat_thread.start()
            self.monitor_thread(chat_thread)

            self.geometry("1640x1040")
        else:
            messagebox.showerror("Warning", "File extension {} not supported yet".format(file_extension))
            self.display_files(self.current_path)


if __name__ == "__main__":
    app = FileSense()
    app.mainloop()