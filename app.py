import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import json
import webbrowser
from chat import summarize_document
from preprocessor import Preprocessor

response = \
"""
{
    "summary": "The file contains a 7-day travel itinerary for New Zealand, starting from October 1, 2024. The itinerary begins with arrival in Auckland and includes visits to key destinations such as Rotorua, Taupo, and Wellington.",
    "actions":
    [
        {
            "action": "renaming",
            "suggest": "2024_10_New_Zealand_Travel_Itinerary"
        },
        {
            "action": "todo",
            "suggest": {
                "status": "Pending",
                "title": "Book Hotels in Rotorua and Wellington",
                "importance": "High",
                "isReminderOn": true,
                "categories": ["Travel", "Accommodation"]
            }
        },
        {
            "action": "todo",
            "suggest": {
                "status": "Pending",
                "title": "Reserve Rental Car",
                "importance": "High",
                "isReminderOn": true,
                "categories": ["Travel", "Transportation"]
            }
        },
        {
            "action": "todo",
            "suggest": {
                "status": "Pending",
                "title": "Pack Hiking Gear",
                "importance": "Medium",
                "isReminderOn": false,
                "categories": ["Packing", "Travel"]
            }
        },
        {
            "action": "mail",
            "suggest": {
                "title": "New Zealand Travel Plans",
                "body": "Hey, just wanted to share our finalized 7-day New Zealand itinerary starting October 1, 2024. Please review and let me know if you have any suggestions or changes!"
            }
        }
    ]
}
"""

class FileSense(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Sense")
        self.geometry("840x1040+50+50")
        self.resizable(False, False)

        # Hide titlebar
        # self.overrideredirect(True)

        self.current_path = os.path.expanduser("~")

        # Init variable
        self.var_address = tk.StringVar()
        self.var_address.set(self.current_path)

        # Init frames
        self.labelframe_explorer = tk.LabelFrame(self, text = "Explorer", height = 1000, width = 800)
        self.labelframe_explorer.place(x = 20, y = 20)
        tk.Label(self.labelframe_explorer, textvariable = self.var_address, anchor="w", justify = tk.LEFT).place(x = 20, y = 20)
        self.frame_files = tk.Frame(self.labelframe_explorer, height = 800, width = 760)
        self.frame_files.place(x = 20, y = 60)
        self.display_files(os.path.expanduser("~"))

        self.frame_senses = tk.Frame(self, height = 1000, width = 800)
        self.frame_senses.place(x = 840, y = 20)
        self.labelframe_preview = tk.LabelFrame(self.frame_senses, text = "Preview")
        self.labelframe_preview.pack(side = tk.TOP, fill = tk.BOTH, expand = False, pady = 8)
        self.labelframe_summary = tk.LabelFrame(self.frame_senses, text = "Summary")
        self.labelframe_summary.pack(side = tk.TOP, fill = tk.BOTH, expand = False, pady = 8)
        self.labelframe_sense = tk.LabelFrame(self.frame_senses, text = "Sense")
        self.labelframe_sense.pack(side = tk.TOP, fill = tk.BOTH, expand = True, pady = 8)

        tk.LabelFrame(self.frame_senses, text = "t").pack(side = tk.TOP, fill = tk.BOTH, expand = True)

    def display_files(self, path):

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
            on_item_click(os.path.expanduser("~"))
            return

        for idx, item in enumerate(items):
            item_path = os.path.abspath(os.path.join(path, item))
            icon = Image.open("./resources/folder.png") if os.path.isdir(item_path) else Image.open("./resources/file.png")
            icon = ImageTk.PhotoImage(icon.resize((40, 40)))
            button = tk.Button(self.frame_files, text = item, image = icon, compound = "top", command = lambda p=item_path: on_item_click(p), height = 80, width = 80, background = "#f0f0f0", borderwidth = 0)
            button.image = icon
            button.grid(row = idx // 7, column = idx % 7, padx = 10, pady = 10)

    def preview_file(self, path):
        def mailto(mailto_uri):
            webbrowser.open(mailto_uri)
        def not_implemented():
            messagebox.showerror("Warning", "Action not supported yet")

        _, file_extension = os.path.splitext(path)
        if file_extension in [".txt", ".py", ".ini", ".pdf", ".xlsx", ".xls", ".doc", ".docx", ".md"]:
            content = Preprocessor.create(path).process()

            # TODO: need integrate with GPT response
            summary = summarize_document(path)
            payload = json.loads(summary)
            summary = payload["summary"]
            actions = payload["actions"]

            scrolledtext_preview = scrolledtext.ScrolledText(self.labelframe_preview, height = 32, width = 94, wrap = tk.WORD, background = "#f0f0f0", borderwidth = 0, state = tk.NORMAL)
            scrolledtext_preview.insert(tk.END, content)
            scrolledtext_preview.configure(state = tk.DISABLED)
            scrolledtext_preview.pack()

            scrolledtext_summary = scrolledtext.ScrolledText(self.labelframe_summary, height = 12, width = 94, wrap = tk.WORD, background = "#f0f0f0", borderwidth = 0, state = tk.NORMAL)
            scrolledtext_summary.insert(tk.END, summary)
            scrolledtext_summary.configure(state = tk.DISABLED)
            scrolledtext_summary.pack()

            # TODO: need integrate with GPT response
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

            tk.Frame(self.labelframe_sense).pack(fill = tk.BOTH, expand = True)

            self.geometry("1640x1040")
        else:
            messagebox.showerror("Warning", "File extension {} not supported yet".format(file_extension))
            self.display_files(self.current_path)


if __name__ == "__main__":
    app = FileSense()
    app.mainloop()