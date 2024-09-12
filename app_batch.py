import os, time, random
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from threading import Thread

from chat import get_document_suggest_naming
from preprocessor import Preprocessor

SUPPORTED_FILE_EXTENSIONS = [".txt", ".pdf", ".xlsx", ".xls", ".doc", ".docx", ".md"]
STATUS_SUPPORTED_FILE_EXTENSIONS = [".xlsx"]
THREAD_CHECK_INTERVAL = 100 # millisecond
COLOR_TRANSPARENT = "#f0f0f0"
# Base on Current UI, we can only drag and drop 7 files at a time
MAX_BATCH_FILES_COUNT = 7

class Status:
    Normal = 0,
    Loading = 1,
    Loaded = 2

# Async Call get suggest naming
class AsyncCall(Thread):
    def __init__(self, content):
        super().__init__()
        self.content = content
    def run(self):
        self.response = get_document_suggest_naming(self.content)

class FileSenseHelper:
    @staticmethod
    def split_full_path(full_path):
        directory_name, file_name = os.path.split(full_path)
        file_name_without_extension, file_extension = os.path.splitext(file_name)
        return directory_name, file_name_without_extension, file_extension

    @staticmethod
    def get_icon(full_path, status = Status.Normal):
        def get_icon_name_without_extension():
            if os.path.isdir(full_path):
                return "folder"
            _, _, file_extension = FileSenseHelper.split_full_path(full_path)
            if file_extension.lower() in STATUS_SUPPORTED_FILE_EXTENSIONS:
                return file_extension[1:].lower() + '_' + status.lower()
            if file_extension.lower() in SUPPORTED_FILE_EXTENSIONS:
                return file_extension[1:].lower()
            return "file"
        return ImageTk.PhotoImage(Image.open("./resources/icons/{}.png".format(get_icon_name_without_extension())).resize((60, 60)))

    @staticmethod
    def is_extension_supported(full_path):
        _, _, file_extension = FileSenseHelper.split_full_path(full_path)
        return file_extension.lower() in SUPPORTED_FILE_EXTENSIONS

class FileSense(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FileSense")
        self.geometry("1260x1040+40+40")
        self.resizable(False, False)

        self.window_log = None
        self.bind("<Control-l>", self.toggle_logging_window)

        # Init variables
        self.current_path = os.getcwd()
        self.var_address = tk.StringVar(value = os.getcwd())
        self.var_theme = tk.StringVar(value = "Travel")
        self.var_animation = tk.StringVar(value = "░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒")
        self.batch_files = []
        self.map_async_tasks = {}

        # Init frames
        self.init_explorer()
        self.init_batch()
        self.update_explorer(os.getcwd())

    log = lambda self, msg: self.text_log.insert(tk.END, msg + '\n') if self.window_log is not None else None

    def init_explorer(self):
        self.labelframe_explorer = tk.LabelFrame(self, text = "Explorer", height = 1000, width = 600)
        self.labelframe_explorer.place(x = 20, y = 20)
        self.label_address = tk.Label(self.labelframe_explorer, text = "Path:")
        self.label_address.place(x = 30, y = 20)
        self.entry_address = tk.Entry(self.labelframe_explorer, textvariable = self.var_address, width = 80, background = COLOR_TRANSPARENT, borderwidth = 1)
        self.entry_address.bind('<Return>', self.update_address)
        self.entry_address.place(x = 70, y = 20)
        self.frame_files = tk.Frame(self.labelframe_explorer, height = 920, width = 560)
        self.frame_files.place(x = 20, y = 60)
        self.canvas_drop_zone = None

    # Wait for migration
    def init_sense(self):
        self.frame_senses = tk.Frame(self, height = 1000, width = 800)
        self.frame_senses.place(x = 640, y = 20)
        self.labelframe_preview = tk.LabelFrame(self.frame_senses, text = "Preview", height = 400, width = 800)
        self.labelframe_preview.pack(fill = tk.BOTH, expand = False)
        self.labelframe_summary = tk.LabelFrame(self.frame_senses, text = "Summary", height = 300, width = 800)
        self.labelframe_summary.pack(fill = tk.BOTH, expand = True, pady = 20)
        self.labelframe_sense = tk.LabelFrame(self.frame_senses, text = "Sense", height = 400, width = 800)
        self.labelframe_sense.pack(side = tk.BOTTOM, fill = tk.BOTH, expand = True)

    
    def init_batch(self):
        self.labelframe_batch = tk.LabelFrame(self, text = "Batch Renaming", height = 1000, width = 600)
        self.labelframe_batch.place(x = 640, y = 20)
        self.label_theme = tk.Label(self.labelframe_batch, text = "Theme:")
        self.label_theme.place(x = 30, y = 20)
        self.entry_theme = tk.Entry(self.labelframe_batch, textvariable = self.var_theme, width = 20, background = COLOR_TRANSPARENT, borderwidth = 1)
        self.entry_theme.place(x = 90, y = 20)
        self.frame_batch_files = tk.Frame(self.labelframe_batch, height = 700, width = 560, borderwidth = 1)
        self.frame_batch_files.place(x = 20, y = 60)
        self.checkbox_move = tk.Checkbutton(self.labelframe_batch, text = "Move into folder",  font = ("Arial", 12))
        self.checkbox_move.place(x = 30, y = 800)
        self.button_confirm = tk.Button(self.labelframe_batch, text = "Confirm", font = ("Arial", 14), width = 48)
        self.button_confirm.place(x = 30, y = 900)


    def remove_batch_file(self, event, file):
        if file in self.batch_files:
            self.batch_files.remove(file)
        self.update_batch_files()

    def update_batch_files(self):
        self.log("Update batch files")
        for widget in self.frame_batch_files.winfo_children():
            widget.destroy()
        for idx, file in enumerate(self.batch_files):
            status = Status.Loaded if self.map_async_tasks.get(file, None) is not None else Status.Loading
            _, file_name_without_extension, file_extension = FileSenseHelper.split_full_path(file)
            icon = FileSenseHelper.get_icon(file, status)

            frame_batch_file = tk.Frame(self.frame_batch_files, height = 100, width = 520)
            frame_batch_file.place(x = 20, y = idx * 100)

            label = tk.Label(frame_batch_file, image = icon, compound = "top", height = 80, width = 80, background = COLOR_TRANSPARENT, borderwidth = 0)
            label.image = icon
            label.place(x = 30, y = 5)
            tk.Label(frame_batch_file, text = file_name_without_extension, compound = "top", height = 2, width = 50, background = COLOR_TRANSPARENT, borderwidth = 0, anchor = "w")\
                .place(x = 130, y = 5)
            button = tk.Label(frame_batch_file, text = "Remove", compound = "top", height = 2, width = 20, background = COLOR_TRANSPARENT, borderwidth = 0, anchor = "w")
            button.place(x = 320, y = 5)
            button.bind("<Button-1>", lambda event, file = file: self.remove_batch_file(event, file))
            if status == Status.Loading:
                tk.Label(frame_batch_file, text = "Generating!", compound = "top", height = 2, width = 20, background = COLOR_TRANSPARENT, borderwidth = 0, anchor = "w")\
                    .place(x = 320, y = 50)
            else:
                tk.Label(frame_batch_file, text = self.map_async_tasks[file], compound = "top", height = 2, width = 50, background = COLOR_TRANSPARENT, borderwidth = 0, anchor = "w")\
                    .place(x = 130, y = 50)
                button_regenerate = tk.Label(frame_batch_file, text = "Regenerate", compound = "top", height = 2, width = 15, background = COLOR_TRANSPARENT, borderwidth = 0, anchor = "w")
                button_regenerate.place(x = 320, y = 50)
                button_regenerate.bind("<Button-1>", lambda event, file = file: self.get_suggest_naming(file, force = True))

    def toggle_logging_window(self, event):
        if self.window_log is None:
            self.window_log = tk.Toplevel(self)
            self.window_log.title("Log")
            self.text_log = tk.Text(self.window_log, height = 60, width = 80)
            self.text_log.pack()
        else:
            self.window_log.destroy()
            self.window_log = None

    def update_explorer(self, path):
        self.log("Update explorer with path {}".format(path))
        self.current_path = os.path.abspath(path)
        self.var_address.set(self.current_path)
        try:
            items = [os.pardir] + os.listdir(path)
        except PermissionError:
            messagebox.showerror("Error", "You do not have permission to access this folder.")
            return
        self.show_items(path, items)
        
    def show_items(self, path, items):
        def drag_start(event):
            self.log("Drag start")
            if self.canvas_drop_zone is None:
                self.canvas_drop_zone = tk.Canvas(self.frame_files, width = 560, height = 200)
                self.canvas_drop_zone.place(x = 0, y = 710)
                self.canvas_drop_zone.create_rectangle(10, 10, 550, 190, dash = (2, 2))
                tk.Label(self.canvas_drop_zone, text="Drop here to start batch renaming").place(x = 190, y = 90)
            event.widget.tkraise()
            event.widget.x, event.widget.y = event.widget.winfo_x(), event.widget.winfo_y()
            event.widget.start_x, event.widget.start_y = event.x, event.y

        def drag_motion(event):
            event.widget.place(x = event.widget.winfo_x() - event.widget.start_x + event.x, y = event.widget.winfo_y() - event.widget.start_y + event.y)

        def drag_end(event, full_path):
            self.log("Drag end")
            if self.canvas_drop_zone is not None:
                self.canvas_drop_zone.destroy()
                self.canvas_drop_zone = None
            event.widget.place(x = event.widget.x, y = event.widget.y)
            if event.widget.winfo_x() > 10 and event.widget.winfo_x() < 550 and event.widget.winfo_y() > 710 and event.widget.winfo_y() < 900:    
                if full_path not in self.batch_files:
                    self.batch_files.append(full_path)
                    self.get_suggest_naming(full_path)
                    self.update_batch_files()

        def on_item_click(path):
            if os.path.isdir(path):
                for widget in self.frame_files.winfo_children():
                    widget.destroy()
                self.update_explorer(path)
            # else:
            #     self.update_file(path)

        truncate_name = lambda name: name if len(name) < 15 else name[:12] + "..."

        self.log("Show items in path {}".format(path))
        for idx, item in enumerate(items):
            full_path = os.path.abspath(os.path.join(path, item))
            icon = FileSenseHelper.get_icon(full_path)

            label = tk.Label(self.frame_files, text = truncate_name(item), image = icon, compound = "top", height = 80, width = 80, borderwidth = 0)
            label.image = icon
            if FileSenseHelper.is_extension_supported(full_path):
                label.bind("<ButtonPress-1>", drag_start)
                label.bind("<B1-Motion>", drag_motion)
                label.bind("<ButtonRelease-1>", lambda event, full_path = full_path: drag_end(event, full_path))
            if os.path.isdir(full_path):
                label.bind("<Button-1>", lambda event, path = full_path: on_item_click(path))
            label.place(x = (idx % 5) * 110, y = (idx // 5) * 110)
    
    def update_address(self, path):
        self.log("Update address to {}".format(self.var_address.get()))
        path = self.var_address.get()
        for widget in self.frame_files.winfo_children():
            widget.destroy()
        if not os.path.isdir(path):
            self.log("Path {} is not a directory".format(path))
            self.update_explorer(self.current_path)
            return
        self.update_explorer(path)

    def get_suggest_naming(self, full_path, force = False):
        def monitor_thread(thread):
            if thread.is_alive():
                self.after(THREAD_CHECK_INTERVAL, lambda: monitor_thread(thread))
            else:
                self.log("Thread finished, get suggest naming {} for file\n {}".format(thread.response, full_path))
                self.map_async_tasks[full_path] = thread.response
                self.update_batch_files()

        if not force and self.map_async_tasks.get(full_path, None) != None:
            return
        if force:
            self.map_async_tasks.pop(full_path)
            self.update_batch_files()
        content = Preprocessor.create(full_path).process()
        thread = AsyncCall(content)
        thread.start()
        monitor_thread(thread)

if __name__ == "__main__":
    app = FileSense()
    app.mainloop()