import os, time, asyncio, re
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from threading import Thread
from dataclasses import dataclass
from enum import Enum

from chat import get_document_suggest_naming, get_folder_suggest_naming
from preprocessor import Preprocessor

SUPPORTED_TEXT_EXTENSIONS = [".txt", ".pdf", ".xlsx", ".xls", ".doc", ".docx", ".md"]
SUPPORTED_IMG_EXTENSIONS = [".png", ".gif", ".jpg", ".jpeg", ".bmp"]
SUPPORTED_FILE_EXTENSIONS = SUPPORTED_TEXT_EXTENSIONS + SUPPORTED_IMG_EXTENSIONS

# TODO: Add more supported extensions
STATUS_SUPPORTED_EXTENSIONS = [".xlsx"]

THREAD_CHECK_INTERVAL = 500 # millisecond
MAX_BATCH_FILE_NUMBER = 7

RESOURCE_ICON_FORMAT = "./resources/icons/{}.png"

class Status(Enum):
    Normal = 1
    Loading = 2
    Loaded = 3

def run_async(callback):
    def inner(func):
        def wrapper(*args, **kwargs):
            def __exec():
                out = func(*args, **kwargs)
                callback(out)
                return out
            return asyncio.get_event_loop().run_in_executor(None, __exec)
        return wrapper
    return inner

@dataclass
class BatchFile:
    full_path: str
    icon: ImageTk.PhotoImage
    content: str
    status: Status
    suggest_name: str
    var_new_name: tk.StringVar
    frame: tk.Frame = None
    need_update: bool = False

class BatchFileHelper:
    @staticmethod
    def from_full_path(full_path: str):
        return BatchFile(full_path, FileSenseHelper.get_file_icon(full_path), Preprocessor.create(full_path).process(), Status.Normal, None, tk.StringVar())

    @staticmethod
    def callback_get_file_suggest_name(*args):
        file, suggest_name = args[0]
        file.status = Status.Loaded
        # Remove invalid characters for file name
        suggest_name = re.sub(r'[/:*?"<>|]', '', suggest_name)
        file.suggest_name = suggest_name
        file.need_update = True
        file.var_new_name.set(suggest_name)
        for widget in file.frame.winfo_children():
            if widget.widgetName == "entry":
                widget.config(state = tk.NORMAL)

    @staticmethod
    @run_async(callback_get_file_suggest_name)
    def get_file_suggest_name(file: BatchFile):
        file.status = Status.Loading
        file.var_new_name.set("Gererating...")
        if file.frame is not None:
            for widget in file.frame.winfo_children():
                if widget.widgetName == "entry":
                    widget.config(state = tk.DISABLED)
        file.need_update = True
        return [file, get_document_suggest_naming(file.content)]

    @staticmethod
    def callback_get_folder_suggest_name(*args):
        variable, entry, suggest_name = args[0]
        variable.set(suggest_name)
        entry.config(state = tk.NORMAL)

    @staticmethod
    @run_async(callback_get_folder_suggest_name)
    def get_folder_suggest_name(file_names, entry, variable):
        entry.config(state = tk.DISABLED)
        return [variable, entry, get_folder_suggest_naming(file_names)]

class FileSenseHelper:
    @staticmethod
    def split_full_path(full_path):
        directory_name, file_name = os.path.split(full_path)
        file_name_without_extension, file_extension = os.path.splitext(file_name)
        return directory_name, file_name_without_extension, file_extension

    @staticmethod
    def get_file_icon(full_path, status = Status.Normal):
        def get_extension_icon_path():
            if os.path.isdir(full_path):
                return RESOURCE_ICON_FORMAT.format("folder")
            _, _, file_extension = FileSenseHelper.split_full_path(full_path)
            if file_extension.lower() in STATUS_SUPPORTED_EXTENSIONS:
                return RESOURCE_ICON_FORMAT.format(file_extension[1:].lower() + '_' + status.name.lower())
            if file_extension.lower() in SUPPORTED_TEXT_EXTENSIONS:
                return RESOURCE_ICON_FORMAT.format(file_extension[1:].lower())
            return RESOURCE_ICON_FORMAT.format("file")

        _, _, file_extension = FileSenseHelper.split_full_path(full_path)
        icon_path = full_path if file_extension.lower() in SUPPORTED_IMG_EXTENSIONS else get_extension_icon_path()
        return ImageTk.PhotoImage(Image.open(icon_path).resize((60, 60)))

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
        self.window_tooltip = None
        self.bind("<Control-l>", self.toggle_logging_window)

        self.current_path = os.getcwd()
        self.var_address = tk.StringVar(value = os.getcwd())
        self.var_move = tk.BooleanVar(value = False)
        self.var_folder = tk.StringVar(value = "")
        self.batch_files = {}
        self.map_async_tasks = {}

        self.init_explorer()
        self.init_batch()
        self.update_explorer(os.getcwd())

    log = lambda self, msg: self.text_log.insert(tk.END, msg + '\n') if self.window_log is not None else None

    def init_explorer(self):
        self.labelframe_explorer = tk.LabelFrame(self, text = "Explorer", height = 1000, width = 600)
        self.labelframe_explorer.place(x = 20, y = 20)
        self.label_address = tk.Label(self.labelframe_explorer, text = "Path:")
        self.label_address.place(x = 30, y = 20)
        self.entry_address = tk.Entry(self.labelframe_explorer, textvariable = self.var_address, width = 80, borderwidth = 1)
        self.entry_address.bind('<Return>', self.update_address)
        self.entry_address.place(x = 70, y = 20)
        self.frame_files = tk.Frame(self.labelframe_explorer, height = 920, width = 560)
        self.frame_files.place(x = 20, y = 60)
        self.canvas_drop_zone = None

    def init_batch(self):
        self.labelframe_batch = tk.LabelFrame(self, text = "Batch Renaming", height = 1000, width = 600)
        self.labelframe_batch.place(x = 640, y = 20)
        self.frame_batch_files = tk.Frame(self.labelframe_batch, height = 790, width = 560, borderwidth = 1, highlightbackground = "gray", highlightthickness = 2)
        self.frame_batch_files.place(x = 20, y = 20)
        self.checkbox_move = tk.Checkbutton(self.labelframe_batch, text = "Move into folder", variable = self.var_move, font = ("Arial", 12), command = self.update_move_folder)
        self.checkbox_move.place(x = 30, y = 850)
        self.entry_folder = tk.Entry(self.labelframe_batch, textvariable = self.var_folder, font = ("Arial", 12), width = 40, borderwidth = 1)
        self.button_confirm = tk.Button(self.labelframe_batch, text = "Confirm", font = ("Arial", 14), width = 48, command = self.rename_batch_files)
        self.button_confirm.place(x = 30, y = 900)
        self.update_batch_files()

    def update_move_folder(self):
        _status = self.var_move.get()
        if _status == True:
            self.var_folder.set("Generating")
            self.entry_folder.place(x = 200, y = 850)
            BatchFileHelper.get_folder_suggest_name([file.var_new_name.get() for file in self.batch_files.values()], self.entry_folder, self.var_folder)
        else:
            self.entry_folder.place_forget()

    def show_tooltip(self, tooltip):
        self.window_tooltip = tk.Toplevel(self)
        tooltip_label = tk.Label(self.window_tooltip, text = tooltip)
        tooltip_label.pack()
        self.window_tooltip.overrideredirect(True)
        x = self.winfo_pointerx() + 20
        y = self.winfo_pointery() + 20
        self.window_tooltip.geometry("+{}+{}".format(x, y))

    def hide_tooltip(self):
        if self.window_tooltip:
            self.window_tooltip.destroy()
            self.window_tooltip = None

    def rename_batch_files(self):
        self.log("Rename batch files")
        _status = self.var_move.get()
        if _status:
            if not os.path.exists(os.path.join(self.current_path, self.var_folder.get())):
                os.makedirs(os.path.join(self.current_path, self.var_folder.get()))
        for file in self.batch_files.values():
            if file.status != Status.Loaded:
                messagebox.showerror("Error", "Please wait for all files to be loaded")
                return
        _keys = list(self.batch_files.keys())
        for full_path in _keys:
            file = self.batch_files[full_path]
            old_name = file.full_path
            directory_name, file_name_without_extension, file_extension = FileSenseHelper.split_full_path(file.full_path)
            if _status:
                directory_name = os.path.join(self.current_path, self.var_folder.get())
            new_name = os.path.join(directory_name, file.var_new_name.get() + file_extension)
            try:
                os.rename(old_name, new_name)
                self.remove_batch_file(file)
                self.log("Rename {} to {}".format(old_name, new_name))
            except  WindowsError:
                messagebox.showerror("Error", "Cannot rename {} to {}".format(old_name, new_name))
        if _status:
            self.checkbox_move.deselect()
            self.var_folder.set("")
        self.update_explorer(self.current_path)

    def remove_batch_file(self, file):
        file.frame.destroy()
        self.batch_files.pop(file.full_path)

    def update_batch_files(self):
        for idx, file in enumerate(self.batch_files.values()):
            if file.need_update:
                if file.status == Status.Loading:
                    file.button_regenerate.place_forget()
                if file.status == Status.Loaded:
                    file.button_regenerate.place(x = 480, y = 45)
                file.need_update = False
            file.frame.place(x = 10, y = idx * 110 + 10)
        self.after(THREAD_CHECK_INTERVAL, self.update_batch_files)

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
        self.hide_tooltip()
        if not os.path.isdir(path):
            self.log("Path {} is not a folder".format(path))
            return
        self.log("Update explorer with path {}".format(path))
        for widget in self.frame_files.winfo_children():
            widget.destroy()
        self.current_path = os.path.abspath(path)
        self.var_address.set(self.current_path)
        try:
            items = [os.pardir] + os.listdir(path)
            self.show_items(path, items)
        except PermissionError:
            messagebox.showerror("Error", "You do not have permission to access this folder.")
            return

    def create_batch_item_frame(self, file):
        file.frame = tk.Frame(self.frame_batch_files, height = 100, width = 540)
        label_icon = tk.Label(file.frame, image = file.icon, compound = "top", height = 80, width = 80, borderwidth = 0)
        label_icon.image = file.icon
        label_icon.place(x = 40, y = 10)
        _,file_name, _ = FileSenseHelper.split_full_path(file.full_path)
        label_old_name = tk.Label(file.frame, text = file_name, compound = "top", height = 2, width = 50, borderwidth = 0, anchor = "w")
        label_old_name.place(x = 140, y = 15)
        label_icon = tk.Label(file.frame, image = file.icon, compound = "top", height = 80, width = 80, borderwidth = 0)
        label_icon.image = file.icon
        label_icon.place(x = 40, y = 15)

        ICON_REMOVE = ImageTk.PhotoImage(Image.open(RESOURCE_ICON_FORMAT.format("remove")).resize((20, 20)))
        button_remove = tk.Label(file.frame, image = ICON_REMOVE, compound = "top", height = 20, width = 20, borderwidth = 0)
        button_remove.image = ICON_REMOVE
        button_remove.place(x = 10, y = 42)
        button_remove.bind("<Button-1>", lambda event, file = file: self.remove_batch_file(file))
        entry_new_name = tk.Entry(file.frame, textvariable = file.var_new_name, width = 50, state = tk.DISABLED)
        entry_new_name.place(x = 140, y = 50)

        ICON_REGENERATE = ImageTk.PhotoImage(Image.open(RESOURCE_ICON_FORMAT.format("regenerate")).resize((20, 20)))
        file.button_regenerate = tk.Label(file.frame, text = "Regenerate", image = ICON_REGENERATE, anchor = "e")
        file.button_regenerate.image = ICON_REGENERATE
        file.button_regenerate.place(x = 480, y = 50)
        file.button_regenerate.bind("<Button-1>", lambda event, file = file: BatchFileHelper.get_file_suggest_name(file))
        file.button_regenerate.place_forget()

    def show_items(self, path, items):
        def drag_start(event):
            self.hide_tooltip()
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
            self.hide_tooltip()
            event.widget.place(x = event.widget.winfo_x() - event.widget.start_x + event.x, y = event.widget.winfo_y() - event.widget.start_y + event.y)

        def drag_end(event, full_path: str):
            self.hide_tooltip()
            self.log("Drag end")
            if self.canvas_drop_zone is not None:
                self.canvas_drop_zone.destroy()
                self.canvas_drop_zone = None
            try:
                event.widget.place(x = event.widget.x, y = event.widget.y)
            except:
                pass
            x, y = event.widget.winfo_x() - event.widget.start_x + event.x, event.widget.winfo_y() - event.widget.start_y + event.y
            if x > 10 and x < 550 and y > 710 and y < 900:
                if full_path in self.batch_files.keys() or len(self.batch_files) >= MAX_BATCH_FILE_NUMBER:
                    return
                file = BatchFileHelper.from_full_path(full_path)
                self.batch_files[full_path] = file
                self.create_batch_item_frame(file)
                BatchFileHelper.get_file_suggest_name(file)

        self.log("Show items in path {}".format(path))
        for idx, item in enumerate(items):
            full_path = os.path.abspath(os.path.join(path, item))
            icon = FileSenseHelper.get_file_icon(full_path)
            label = tk.Label(self.frame_files, text = item, wraplength = 60, image = icon, compound = "top", height = 78, width = 78, borderwidth = 0, anchor = "n")
            label.image = icon
            label.bind("<Enter>", lambda event, tooltip = item: self.show_tooltip(tooltip))
            label.bind("<Leave>", lambda event: self.hide_tooltip())
            if FileSenseHelper.is_extension_supported(full_path):
                label.bind("<ButtonPress-1>", drag_start)
                label.bind("<B1-Motion>", drag_motion)
                label.bind("<ButtonRelease-1>", lambda event, full_path = full_path: drag_end(event, full_path))
            if os.path.isdir(full_path):
                label.bind("<Button-1>", lambda event, path = full_path: self.update_explorer(path))
            label.place(x = (idx % 5) * 110, y = (idx // 5) * 110)

    def update_address(self, event):
        path = self.var_address.get()
        self.log("Update address to {}".format(path))
        if not os.path.isdir(path):
            self.log("Path {} is not a directory".format(path))
            self.update_explorer(self.current_path)
            return
        self.update_explorer(path)

if __name__ == "__main__":
    app = FileSense()
    app.mainloop()