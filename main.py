import os
import sys
import shutil
import json
import pygame
import sounddevice as sd
import playsound
import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from pynput.keyboard import Listener
from PIL import Image, ImageDraw
import pystray
import threading


dir_ = "sound" # Soundboard directory path
config = "config.json" # Config file path
hotkeys = {}
menu = []
volume_level = 1.0
play_score = 0 # Total plays of soundboard


def find_device(): # Find VB Audio Virtual Cable device
    devices = sd.query_devices()
    target_device_name = "CABLE Input (VB-Audio Virtual Cable)"
    for idx, device in enumerate(devices):
        if device["name"] == target_device_name:
            print(f"Using audio device: {device['name']} (Index: {idx})")
            pygame.mixer.quit()
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048, devicename=device["name"])
            return

    messagebox.showerror("Error", "VB Audio Virtual Cable not found. Install it.")
    sys.exit()


def get_files(dir_, config): # Get sound files from directory
    global play_score
    if not os.path.exists(dir_): # Create sound directory if not exists
        os.mkdir(dir_)

    if os.path.exists(config): # Load sound data from config file
        sound_data = json.load(open(config))
        global hotkeys, menu
        hotkeys = sound_data.get("hotkeys", {})
        menu = sound_data.get("sounds", [])
        play_score = sound_data.get("play_score", 0)

    else:
        menu = []
        sound_data = {"hotkeys": {}, "sounds": [], "play_score": 0}
        json.dump(sound_data, open(config, "w"))

    if len(os.listdir(dir_)) == 0:
        messagebox.showinfo("Sounds!", "Drag and drop sound files :)")
        pass

    sounds = [] # Sounds list
    sounds_list = [dir_]

    for item in os.listdir(dir_): # Get sound files from directory
        path = os.path.join(dir_, item)

        if os.path.isfile(path):
            if os.path.splitext(item)[1] in [".wav", ".mp3", ".m4a"]:
                sounds_list.append(item)

        elif os.path.isdir(path):
            sounds_list_get = [path]

            for sitem in os.listdir(path):
                spath = os.path.join(path, sitem)
                
                if os.path.isfile(spath):
                    if os.path.splitext(sitem)[1] in [".wav", ".mp3", ".m4a"]:
                        sounds_list_get.append(sitem)

            if len(sounds_list_get) > 1:
                sounds.append(sounds_list_get)

    if len(sounds_list) > 1:
        sounds.append(sounds_list)

    menu = sounds
    sound_data["sounds"] = sounds
    json.dump(sound_data, open(config, "w"))


def play_sound(sound=None): # Play sound
    global play_score
    def pygame_sound(): # Play sound using pygame
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(sound)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

        except Exception as e:
            print(f"Pygame error: {e}")
    
    def playsound_audio(): # Play sound using playsound
        try:
            playsound.playsound(sound)

        except Exception as e:
            print(f"Playsound error: {e}")

    play_score += 1
    save()

    threading.Thread(target=pygame_sound, daemon=True).start()
    threading.Thread(target=playsound_audio, daemon=True).start()


def stop_sound(): # Stop sound playback
    pygame.mixer.music.stop()


def set_volume(val): # Set volume level
    global volume_level
    volume_level = float(val) / 100
    pygame.mixer.music.set_volume(volume_level)


def save(): # Save sound data to config file including hotkeys, sounds and play score
    sound_data = {"hotkeys": hotkeys, "sounds": menu, "play_score": play_score}
    json.dump(sound_data, open(config, "w"))


def set_hotkey(sound): # Set hotkey for a sound
    def release(key):
        key_str = str(key).replace("'", "")
        if key_str not in hotkeys:
            hotkeys[key_str] = sound
            save()

        else:
            hotkeys[key_str] = sound
            save()
        
        hotkey_listener.stop()

    hotkey_listener = Listener(on_release=release)
    hotkey_listener.start()


def on_press(key): # On key press event handler for hotkeys
    try:
        key_str = str(key).replace("'", "")
        if key_str in hotkeys: # Play sound if hotkey is pressed
            sound = hotkeys[key_str]
            sound_path = os.path.join(dir_, sound)
            play_sound(sound_path)
            
            save()
            app.update_play_score_label()
            
    except Exception as e:
        print(f"Error on key press: {e}")


def start_hotkey_listener(): # Start hotkey listener
    with Listener(on_press=on_press) as listener:
        listener.join()


def create_image(width, height, color1, color2): # Icon for Tray func
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        [(width // 4, height // 4), (width * 3 // 4, height * 3 // 4)],
        fill=color2
    )
    return image


def minimize_to_tray(app): # Tray func
    app.withdraw()

    def show_app(icon, item): # Show app from tray
        icon.stop()
        app.deiconify()

    def quit_app(icon, item): # Quit app from tray
        icon.stop()
        app.quit()

    menu = pystray.Menu(
        pystray.MenuItem("Show", show_app),
        pystray.MenuItem("Quit", quit_app)
    )

    icon = pystray.Icon(
        "PySoundboard",
        create_image(64, 64, "black", "white"),
        "PySoundboard",
        menu
    )

    icon.run()


class UI(TkinterDnD.Tk): # Main UI class containing all UI elements
    def __init__(self):
        super().__init__()
        self.title("PySoundboard")
        self.geometry("700x500")
        self.iconbitmap("icon.ico")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")

        self.shortcut_ui_instance = None
        self.shortcut_viewer_ui_instance = None

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Assign Shortcut", command=self.open_shortcuts)
        self.context_menu.add_command(label="Clear Shortcut", command=self.clear_selected_shortcut)
        self.context_menu.add_command(label="Delete Soundboard", command=self.delete_selected_sound)

        self.sound_dir_list = ttk.Treeview(self, height=15, columns=("Name", "Size", "Shortcut"), show="headings")
        self.sound_dir_list.heading("Name", text="Name")
        self.sound_dir_list.heading("Size", text="Size")
        self.sound_dir_list.heading("Shortcut", text="Shortcut")
        self.sound_dir_list.column("Name", anchor="w", width=350)
        self.sound_dir_list.column("Size", anchor="center", width=100)
        self.sound_dir_list.column("Shortcut", anchor="center", width=60)
        self.sound_dir_list.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        self.sound_dir_list.bind("<Button-3>", self.show_context_menu)
        self.sound_dir_list.bind("<Double-1>", self.play_selected_double_click)

        volume_label = tk.Label(self, text="Volume in microphone:", bg="#1e1e1e", fg="white", anchor="w")
        volume_label.pack(fill=tk.X, padx=10, pady=5)

        self.volume_slider = tk.Scale(self, from_=0, to=100, orient="horizontal", command=set_volume, bg="#1e1e1e", fg="white")
        self.volume_slider.set(100)
        self.volume_slider.pack(fill=tk.X, padx=10, pady=5)

        play_button = tk.Button(self, text="Play", command=self.play_selected_sound, bg="#007ACC", fg="white")
        play_button.pack(side=tk.LEFT, padx=5, pady=5)
        stop_button = tk.Button(self, text="Stop", command=stop_sound, bg="#007ACC", fg="white")
        stop_button.pack(side=tk.LEFT, padx=5, pady=5)
        shortcut_button = tk.Button(self, text="Shortcuts", command=self.open_all_shortcuts, bg="#007ACC", fg="white")
        shortcut_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.update_sound_dir_list()

        self.sound_dir_list.drop_target_register(DND_FILES)
        self.sound_dir_list.dnd_bind("<<Drop>>", self.handle_drop)

        self.play_score_label = tk.Label(self, text=f"Total Plays: {play_score}", bg="#1e1e1e", fg="white")
        self.play_score_label.pack(side=tk.BOTTOM, anchor="e", padx=10, pady=5)

    def update_play_score_label(self): # Update play score label
        self.play_score_label.config(text=f"Total Plays: {play_score}")

    def show_context_menu(self, event): # Show context menu on right click for deleting soundboard and assigning shortcuts
        item = self.sound_dir_list.identify_row(event.y)
        if item:
            self.context_menu.post(event.x_root, event.y_root)
            self.selected_sound = self.sound_dir_list.item(item)["values"][0]

    def update_sound_dir_list(self): # Update soundboard list
        self.sound_dir_list.delete(*self.sound_dir_list.get_children())

        for category in menu:
            category_name = category[0]

            for sound in category[1:]:
                sound_path = os.path.join(category_name, sound)

                if os.path.isfile(sound_path):
                    size = os.path.getsize(sound_path) / 1048576
                    size_formatted = f"{size:.2f} Mb"

                    shortcut = next(
                        (key for key, value in hotkeys.items() if value == sound),
                        "None"
                    )

                    self.sound_dir_list.insert("", "end", values=(sound, size_formatted, shortcut))

    def handle_drop(self, event): # Drag and drop sound files to add a copy to soundboard directory
        dropped_files = self.tk.splitlist(event.data)
        
        for file_path in dropped_files:

            if os.path.isfile(file_path) and file_path.lower().endswith((".mp3", ".wav", ".m4a")):
                dest_path = os.path.join(dir_, os.path.basename(file_path))
                try:
                    shutil.copy(file_path, dest_path)

                except Exception as e:
                    messagebox.showerror("Error", f"Failed to copy {file_path}: {e}")

        global menu
        get_files(dir_, config)
        self.update_sound_dir_list()

    def update_shortcuts_in_treeview(self): # Update shortcuts in treeview
        for item in self.sound_dir_list.get_children():
            values = self.sound_dir_list.item(item)["values"]
            sound = values[0]
            shortcut = next((key for key, value in hotkeys.items() if value == sound), "None")
            self.sound_dir_list.item(item, values=(values[0], values[1], shortcut))

    def clear_selected_shortcut(self): # Clear shortcut for a sound
        if hasattr(self, 'selected_sound') and self.selected_sound:

            if self.selected_sound in hotkeys.values():
                current_key = next(k for k, v in hotkeys.items() if v == self.selected_sound)
                del hotkeys[current_key]
                save()
                self.update_shortcuts_in_treeview()

            else:
                messagebox.showinfo("Info", f"No shortcut assigned to {self.selected_sound}")
                
        else:
            messagebox.showinfo("Error", "No soundboard selected.")

    def play_selected_sound(self): # Play selected soundboard using play_sound func
        selected_item = self.sound_dir_list.selection()
        if selected_item:
            sound = self.sound_dir_list.item(selected_item)["values"][0]
            play_sound(os.path.join(dir_, sound))
            self.update_play_score_label()

    def play_selected_double_click(self, event): # Play selected soundboard using play_sound func on double click
        selected_item = self.sound_dir_list.selection()
        if selected_item:
            sound = self.sound_dir_list.item(selected_item)["values"][0]
            play_sound(os.path.join(dir_, sound))
            self.update_play_score_label()

    def open_shortcuts(self): # Open shortcut UI to assign shortcuts
        if self.shortcut_ui_instance is None or not self.shortcut_ui_instance.winfo_exists():
            selected_item = self.sound_dir_list.selection()

            if selected_item:
                sound = self.sound_dir_list.item(selected_item)["values"][0]
                self.shortcut_ui_instance = ShortcutUI(self, selected_sound=sound)

            else:
                messagebox.showinfo("Error", "Select a sound first")

        else:
            self.shortcut_ui_instance.lift()

    def open_all_shortcuts(self): # Open shortcut viewer UI to view all shortcuts
        if self.shortcut_viewer_ui_instance is None or not self.shortcut_viewer_ui_instance.winfo_exists():
            self.shortcut_viewer_ui_instance = ShortcutViewerUI(self)

        else:
            self.shortcut_viewer_ui_instance.lift()

    def delete_selected_sound(self): # Delete soundboard from directory
        if hasattr(self, 'selected_sound') and self.selected_sound:
            sound_path = os.path.join(dir_, self.selected_sound)
            
            if os.path.isfile(sound_path):
                try:
                    with open(sound_path, 'r+'):
                        pass
                except OSError:
                    return
                
                try:
                    os.remove(sound_path)

                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete {self.selected_sound}: {e}")
                
                global menu
                get_files(dir_, config)
                self.update_sound_dir_list()
            else:
                messagebox.showerror("Error", "Soundboard file not found.")
        else:
            messagebox.showinfo("Error", "No soundboard selected.")

    def on_close(self): # Minimize to tray
        if self.shortcut_ui_instance and self.shortcut_ui_instance.winfo_exists():
            self.shortcut_ui_instance.destroy()
            self.shortcut_ui_instance = None

        if self.shortcut_viewer_ui_instance and self.shortcut_viewer_ui_instance.winfo_exists():
            self.shortcut_viewer_ui_instance.destroy()
            self.shortcut_viewer_ui_instance = None

        minimize_to_tray(self)


class ShortcutViewerUI(tk.Toplevel): # Shortcut viewer UI class to view all shortcuts
    def __init__(self, master):
        super().__init__(master)
        self.title("Shortcut Viewer")
        self.geometry("400x300")
        self.iconbitmap("icon.ico")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        label = tk.Label(self, text="Assigned Shortcuts", bg="#1e1e1e", fg="white")
        label.pack(pady=10)

        self.shortcuts_listbox = tk.Listbox(self, bg="#1e1e1e", fg="white", selectmode=tk.SINGLE, height=15)
        self.shortcuts_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.update_shortcut_listbox()

    def update_shortcut_listbox(self): # Update shortcuts in listbox
        self.shortcuts_listbox.delete(0, tk.END)

        for key, sound in hotkeys.items():
            self.shortcuts_listbox.insert(tk.END, f"{key}: {sound}")

    def on_close(self): # Close shortcut viewer UI
        self.master.shortcut_viewer_ui_instance = None
        self.destroy()


class ShortcutUI(tk.Toplevel): # Shortcut UI class to assign shortcuts
    def __init__(self, master, selected_sound=None):
        super().__init__(master)
        self.master = master
        self.selected_sound = selected_sound
        self.title("Assign Shortcut")
        self.geometry("300x350")
        self.iconbitmap("icon.ico")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")
        self.selected_sound = selected_sound

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        label = tk.Label(self, text="Current Shortcuts", bg="#1e1e1e", fg="white")
        label.pack(pady=10)

        self.shortcuts_listbox = tk.Listbox(self, bg="#1e1e1e", fg="white", selectmode=tk.SINGLE, height=8)
        self.shortcuts_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.update_shortcut_listbox()

        self.instruction_label = tk.Label(self, text="Click 'Assign New Shortcut' to start", bg="#1e1e1e", fg="white")
        self.instruction_label.pack(pady=5)

        self.selected_sound_label = tk.Label(self, text=f"Selected Sound: {selected_sound}", bg="#1e1e1e", fg="white")
        self.selected_sound_label.pack(pady=5)

        self.assign_button = tk.Button(self, text="Assign New Shortcut", command=self.start_assigning_shortcut, bg="#007ACC", fg="white")
        self.assign_button.pack(pady=5)

        self.delete_button = tk.Button(self, text="Delete", command=self.delete_shortcut, bg="#FF6347", fg="white")
        self.delete_button.pack(pady=5)

    def update_shortcut_listbox(self): # Update shortcuts in listbox
        self.shortcuts_listbox.delete(0, tk.END)

        for key, sound in hotkeys.items():
            self.shortcuts_listbox.insert(tk.END, f"{key}: {sound}")

    def start_assigning_shortcut(self): # Start assigning shortcut to a sound
        if not self.selected_sound:
            messagebox.showerror("Error", "Please select a sound first")
            return

        self.instruction_label.config(text=f"Press a Button to assign to '{self.selected_sound}'")
        self.assign_button.config(state=tk.DISABLED)

        self.listener = Listener(on_press=self.on_key_press)
        self.listener.start()

    def on_key_press(self, key): # On key press event handler for assigning shortcut
        try:
            key_str = str(key).replace("'", "")
            if key_str in hotkeys:

                self.instruction_label.config(text=f"{key_str} already assigned to '{hotkeys[key_str]}'.")
            elif self.selected_sound in hotkeys.values():
                current_key = next(k for k, v in hotkeys.items() if v == self.selected_sound)
                del hotkeys[current_key]  # Remove existing shortcut for this sound
                hotkeys[key_str] = self.selected_sound
                save()
                self.update_shortcut_listbox()

                self.master.update_shortcuts_in_treeview()
                self.instruction_label.config(text=f"Assigned {key_str} to '{self.selected_sound}'")
                
            else:
                hotkeys[key_str] = self.selected_sound
                save()
                self.update_shortcut_listbox()

                self.master.update_shortcuts_in_treeview()
                self.instruction_label.config(text=f"Assigned {key_str} to '{self.selected_sound}'")
            
            self.listener.stop()
            self.assign_button.config(state=tk.NORMAL)

        except Exception as e:
            print(f"Error capturing key press: {e}")

    def delete_shortcut(self): # Delete shortcut for a sound
        selected_index = self.shortcuts_listbox.curselection()
        if selected_index:
            selected_shortcut = self.shortcuts_listbox.get(selected_index)
            key = selected_shortcut.split(":")[0].strip()

            if key in hotkeys:
                del hotkeys[key]
                save()
                self.update_shortcut_listbox()

                self.master.update_shortcuts_in_treeview()

            else:
                messagebox.showerror("Error", "Shortcut not found.")

        else:
            messagebox.showerror("Error", "Please select a shortcut to delete.")

    def on_close(self):
        self.master.shortcut_ui_instance = None
        self.destroy()


if __name__ == "__main__":
    get_files('sound', 'config.json')
    find_device()

    threading.Thread(target=start_hotkey_listener, daemon=True).start()

    app = UI()
    app.mainloop()
