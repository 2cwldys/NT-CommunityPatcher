import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageSequence
import os
import zipfile
import shutil
import pygame
import datetime
import subprocess
import sys

# PyInstaller resource path
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class NTPatcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NEOTOKYO° patcher")
        self.root.geometry("400x200")
        self.root.resizable(False, False)

        # Set window icon
        self.root.iconbitmap(self.resource_path("app_icon.ico"))  # Use resource_path for the icon

        self.game_path = ""
        self.music_playing = True

        # Initialize pygame mixer
        pygame.mixer.init()
        try:
            pygame.mixer.music.load(self.resource_path("music.mp3"))  # Use resource_path for music
            pygame.mixer.music.set_volume(0.05)
            pygame.mixer.music.play(-1)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load music: {e}")

        try:
            self.button_sound = pygame.mixer.Sound(self.resource_path("button.mp3"))  # Use resource_path for button sound
            self.button_sound.set_volume(0.08)  # Set volume to 8%
        except Exception as e:
            self.button_sound = None
            messagebox.showwarning("Warning", f"Failed to load button sound: {e}")

        # Load static background image
        self.bg_image = Image.open(self.resource_path("background.jpg"))
        self.bg_image = self.bg_image.resize((400, 200), Image.Resampling.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)

        self.bg_label = tk.Label(root, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Directory path entry
        self.path_entry = tk.Entry(root, width=30)
        self.path_entry.place(x=100, y=13)

        # Buttons
        button_style = {"bg": "#4A4A4A", "fg": "white", "activebackground": "#4A4A4A", "activeforeground": "white"}
        tk.Button(root, text="Select Path", command=self.with_sound(self.select_path), **button_style).place(x=10, y=10)
        self.music_button = tk.Button(root, text="Music", command=self.with_sound(self.toggle_music), **button_style)
        self.music_button.place(x=330, y=10)
        tk.Button(root, text="Install", command=self.with_sound(self.install_files), **button_style).place(x=10, y=50)
        tk.Button(root, text="Run Neotokyo", command=self.with_sound(self.run_neotokyo), **button_style).place(x=10, y=110)
        tk.Button(root, text="Restore Backup", command=self.with_sound(self.restore_backup), **button_style).place(x=10, y=140)

        # Handling window close and focus properly
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # Handle window close
        self.root.protocol("WM_TAKE_FOCUS", self.on_focus)

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS  # For packaged version
        except Exception:
            base_path = os.path.abspath(".")  # For development version
        return os.path.join(base_path, relative_path)

    def select_path(self):
        path = filedialog.askdirectory()
        if path:
            self.game_path = path
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            messagebox.showinfo("Path Selected", f"Game path set to: {path}")

    def toggle_music(self):
        if pygame.mixer.music.get_busy() or not self.music_playing:
            if self.music_playing:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()
            self.music_playing = not self.music_playing

    def extract_multiple_zips(self, zip_files):
        for zip_file in zip_files:
            # Ensure the zip file exists
            if not os.path.exists(zip_file):
                messagebox.showerror("Error", f"{zip_file} does not exist.")
                continue
            
            # Extract the zip file to the game path
            try:
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    # Extract all files into the game path
                    zip_ref.extractall(self.game_path)
                    print(f"Extracted {zip_file} into {self.game_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract {zip_file}: {e}")
                continue

    def restore_backup(self):
        # Ensure game_path is set
        if not self.game_path:
            messagebox.showerror("Error", "Please select a game path first.")
            return

        # List all .zip files in the game_path directory
        backup_files = [f for f in os.listdir(self.game_path) if f.endswith('.zip')]

        # If no backup files exist, show an error
        if not backup_files:
            messagebox.showerror("Error", "No backup files found in the game directory.")
            return

        # Sort the backup files based on their timestamp in the filename
        try:
            # Extract the timestamp from the filename and sort them in descending order
            backup_files.sort(key=lambda f: datetime.datetime.strptime(f, f'NTSource_backup_%Y%m%d_%H%M%S.zip'), reverse=True)

            # Get the latest backup file
            latest_backup = backup_files[0]
            latest_backup_path = os.path.join(self.game_path, latest_backup)

            # Extract the contents of the latest backup zip file
            with zipfile.ZipFile(latest_backup_path, 'r') as backup_zip:
                backup_zip.extractall(self.game_path)

            print(f"Backup restored from: {latest_backup_path}")
            messagebox.showinfo("Restore Completed", f"Backup restored from {latest_backup}.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore backup: {e}")

    def install_files(self):

        # Ensure game_path is set
        if not self.game_path:
            messagebox.showerror("Error", "Please select a game path first.")
            return

        # Ensure the selected game path contains "NEOTOKYO"
        if "NEOTOKYO" not in os.path.basename(self.game_path):
            messagebox.showerror("Error", "The selected path must contain 'NEOTOKYO'. Please select the correct folder.")
            return

        # Create a backup zip file of the game_path directory before making any changes
        try:
            # Generate a timestamp for the backup file name
            timestamp = datetime.datetime.now().strftime(f"%Y%m%d_%H%M%S")
            backup_zip_name = f"NTSource_backup_{timestamp}.zip"
            backup_zip_path = os.path.join(self.game_path, backup_zip_name)

            response = messagebox.askyesno("Backup Confirmation", f"Do you wish to back up NeotokyoSource? This can protect your base game data...")

            if response:
                messagebox.showinfo("Creating Backup", f"A backup of your NeotokyoSource will take place, this may freeze for a substantial time, please wait for it to finish...\n\nClick to continue...")
                # Create a zip file, excluding the existing backup zip file from being added to it
                with zipfile.ZipFile(backup_zip_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                    for foldername, subfolders, filenames in os.walk(self.game_path):
                        # Exclude the backup zip file from being added to itself
                        if backup_zip_name not in filenames:
                            for filename in filenames:
                                file_path = os.path.join(foldername, filename)
                                # Add file to zip, maintaining directory structure
                                backup_zip.write(file_path, os.path.relpath(file_path, self.game_path))

                print(f"Backup created: {backup_zip_path}")
                messagebox.showinfo("Backup Created", f"To protect your base game assets, {backup_zip_name} has been created in {self.game_path}...")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create a backup: {e}")
            return

        # List of zip files to extract
        zip_files = [
            self.resource_path("NT-IconFix.zip"),
            self.resource_path("TedCustomSounds.zip"),
            self.resource_path("VCROSD_FontMod.zip"),
            self.resource_path("Silenced_MILSO.zip"),
            self.resource_path("RedFragBlueSmoke.zip"),
            self.resource_path("CONFIGS.zip"),
            self.resource_path("FOOTSTEPS.zip"),
            self.resource_path("ZR68_Sounds.zip"),
            self.resource_path("ZR2013.zip")
        ]

        response_streamsafe = messagebox.askyesno("Add STREAMSAFE", "Do you wish to extract streamer-safe overwrites for SFW materials and textures?")

        if response_streamsafe:
            zip_files.append(self.resource_path("STREAMSAFE.zip"))
            print("STREAMSAFE.zip has been added to the list.")

        # Path to client.dll in resources
        client_dll_path = resource_path("client.dll")

        # Extract multiple zips
        self.extract_multiple_zips(zip_files)

        # Define target path for client.dll
        target_dir = os.path.join(self.game_path, "NeotokyoSource", "bin")
        target_dll_path = os.path.join(target_dir, "client.dll")

        # Check if client.dll exists in the resource path
        if not os.path.exists(client_dll_path):
            messagebox.showerror("Error", f"client.dll not found in resources at {client_dll_path}")
            return

        # Check if the target directory exists, create it if it doesn't
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)  # Create 'bin' directory if it doesn't exist
                print(f"Created target directory: {target_dir}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create target directory: {e}")
                return

        # Check if client.dll already exists in the target location
        if not os.path.exists(target_dll_path):
            try:
                # Copy client.dll to the target directory, overwriting if it exists
                shutil.copy(client_dll_path, target_dll_path)
                print(f"client.dll successfully copied to {target_dll_path}.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy client.dll: {e}")
                return
        else:
            shutil.copy(client_dll_path, target_dll_path)
            print(f"client.dll successfully copied to {target_dll_path}.")

        # Determine which script to run
        script_name = "iconfix.bat" if os.name == "nt" else "iconfix.sh"
        script_path = os.path.join(self.game_path, script_name)

        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"Missing {script_name} in extracted files.")
            return

        try:
            # Use Popen to run the batch file
            process = subprocess.Popen(script_path, shell=True, cwd=self.game_path)
            process.communicate()  # Wait for the process to finish and capture output
            # Ignore the error if returncode is 1
            if process.returncode != 0:
                print(f"Warning: {script_name} returned with code {process.returncode}. Ignoring the error.")  # Log the warning
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run {script_name}: {e}")
            return

        # Create a readme_patcher.txt with details of the patches applied
        try:
            readme_file_path = os.path.join(self.game_path, "readme_patcher.txt")
            with open(readme_file_path, "w") as readme_file:
                readme_file.write("NEOTOKYO Patch List:\n")
                readme_file.write("=" * 40 + "\n")
                readme_file.write("1. Extracted and applied the NT-IconFix patch.\n")
                readme_file.write("2. Overwritten existing client.dll for FOV patch in NeotokyoSource/bin.\n")
                readme_file.write("3. Applies OLD 2013 ZR68C, ZR68S, ZR68L weapon models.\n")
                readme_file.write("4. Applies custom silenced recon MILSO model.\n")
                readme_file.write("5. Applies custom sound overrides for all various weapons.\n")
                readme_file.write("6. Applies custom VCR OSD MONO font replacements.\n")
                readme_file.write("7. Applies custom grenade skins to differentiate them easier.\n")
                readme_file.write("8. Adjusts client default config with accurate rates for smoothest play.\n")
                readme_file.write("9. Applies custom footstep sounds for the player.\n")
                readme_file.write("10. Applies new & unique ZR68 weapon sounds.\n")
                readme_file.write("11. Applies toggled crouch & lean alias binds.\n")
                readme_file.write("\n")
                readme_file.write("(OPTIONAL:) If selected, streamsafe materials & textures for SFW twitch streaming.\n")
                readme_file.write("=" * 40 + "\n")
                readme_file.write("FROM: https://bonahnsa.com/mods.html\n")
                readme_file.write("\n")
                readme_file.write("You may run [Restore Backup] after specifying NEOTOKYO game path to restore original files.")
            print(f"Readme file created at: {readme_file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create readme_patcher.txt: {e}")
            return

        readme = messagebox.askyesno("Installation Completed", f"Installation completed successfully.\nReadme of patched changes are in {self.game_path}.\nDo you wish to open them?")
        if readme:
            readme_file_path = os.path.join(self.game_path, "readme_patcher.txt")
            
            if os.path.exists(readme_file_path):
                try:
                    # Determine the operating system
                    if os.name == "nt":  # Windows
                        subprocess.Popen(["notepad.exe", readme_file_path])
                        print(f"Opening {readme_file_path} in Notepad...")
                    else:  # Unix-based systems (Linux, macOS, etc.)
                        subprocess.Popen(["vim", readme_file_path])
                        print(f"Opening {readme_file_path} in Vim...")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open the readme file: {e}")
            else:
                messagebox.showerror("Error", f"The readme file does not exist at {readme_file_path}")
        else:
            pass;

    def run_neotokyo(self):
        if not self.game_path:
            messagebox.showerror("Error", "Please select a game path first.")
            return

        os.startfile("steam://run/244630") # Run NEOTOKYO via Steam URL

    def with_sound(self, func):
        def wrapper(*args, **kwargs):
            if self.button_sound:
                self.button_sound.play()  # Play button sound
            return func(*args, **kwargs)
        return wrapper

    def on_focus(self):
        self.root.lift()

    def on_close(self):
        # Exit gracefully
        pygame.mixer.music.stop()
        self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = NTPatcherApp(root)
    root.mainloop()
