import os 
import tempfile
import requests
import subprocess
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import csv
from metadata_handler import MetadataHandler  # Import the new class
from metadata_ui import MetadataUI  # Import the new UI class

class BlobApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blob File Loader")
        self.root.geometry("800x600")
        self.temp_dir = os.path.join(tempfile.gettempdir(), "BlobAppTemp")
        self.clone_dir = os.path.join(self.temp_dir, "cyz2json")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.clear_temp_folder()

        # Initialize the MetadataHandler
        self.metadata_handler = MetadataHandler(self.temp_dir)
        self.metadata_ui = MetadataUI(self.save_metadata_callback)  # Pass save callback to MetadataUI
        self.metadata_ui.window.withdraw()  # Hide the window initially

        # UI Components
        self.compile_button = tk.Button(root, text="Download and compile cyz2json tool (required)", command=self.compile_cyz2json)
        self.compile_button.pack(pady=10)

        self.path_label = tk.Label(root, text="Path to cyz2json Installation:")
        self.path_label.pack(pady=5)

        self.path_entry = tk.Entry(root, width=100)
        self.path_entry.insert(0, self.clone_dir + "\\bin\\Cyz2Json.dll")
        self.path_entry.pack(pady=5)

        self.url_label = tk.Label(root, text="Blob File URL:")
        self.url_label.pack(pady=5)

        self.url_entry = tk.Entry(root, width=100)
        self.url_entry.insert(0, "https://citprodflowcytosa.blob.core.windows.net/public/ThamesSTN6MA4_9%202023-10-16%2011h24.cyz")
        self.url_entry.pack(pady=5)

        self.download_button = tk.Button(root, text="Download", command=self.download_file)
        self.download_button.pack(pady=10)

        self.load_label = tk.Label(root, text="Load File Path:")
        self.load_label.pack(pady=5)

        self.load_entry = tk.Entry(root, width=100)
        self.load_entry.insert(0, "C:/Users/JR13/Downloads/ThamesSTN6MA4_9%202023-10-16%2011h24.cyz")
        self.downloaded_file = "C:/Users/JR13/Downloads/ThamesSTN6MA4_9%202023-10-16%2011h24.cyz"
        self.load_entry.pack(pady=5)

        self.load_button = tk.Button(root, text="Convert to json", command=self.load_file)
        self.load_button.pack(pady=10)

        self.process_button = tk.Button(root, text="Extract images and associated data", command=self.process_file)
        self.process_button.pack(pady=10)

        self.json_file = os.path.join(self.temp_dir, "tempfile.json")
        self.csv_file = os.path.join(self.temp_dir, "tempfile.csv")

        self.image_label = None
        self.tif_files = []
        self.current_image_index = 0

    def clear_temp_folder(self):
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")

    def compile_cyz2json(self):
        BlobApp.clone_dir = os.path.join(self.temp_dir, "cyz2json")
        if os.path.exists(BlobApp.clone_dir):
            messagebox.showinfo("Info", "cyz2json already exists in " + BlobApp.clone_dir)
            return
        try:
            subprocess.run(["git", "clone", "https://github.com/OBAMANEXT/cyz2json.git", BlobApp.clone_dir], check=True)
            subprocess.run(["dotnet", "build", "-o", "bin"], cwd=BlobApp.clone_dir, check=True)
            messagebox.showinfo("Success", "cyz2json downloaded and compiled successfully!")
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, os.path.join(BlobApp.clone_dir, "bin", "Cyz2Json.dll"))
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Compilation Error", f"Failed to compile cyz2json: {e}. Have you installed the requirement DotNet version 8.0? See https://github.com/OBAMANEXT/cyz2json")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def download_file(self):
        url = self.url_entry.get()
        try:
            response = requests.get(url, allow_redirects=True)
            response.raise_for_status()
            filename = os.path.basename(url)
            self.downloaded_file = os.path.join(self.temp_dir, filename)
            with open(self.downloaded_file, 'wb') as file:
                file.write(response.content)
            self.load_entry.delete(0, tk.END)
            self.load_entry.insert(0, self.downloaded_file)
            messagebox.showinfo("Download Success", f"File downloaded successfully to: {self.downloaded_file}")
        except requests.RequestException as e:
            messagebox.showerror("Download Error", f"Failed to download file: {e}")

    def load_file(self):
        cyz2json_path = self.path_entry.get()
        try:
            subprocess.run(["dotnet", cyz2json_path, self.downloaded_file, "--output", self.json_file], check=True)
            messagebox.showinfo("Success", f"File processed successfully. Output: {self.json_file}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Processing Error", f"Failed to process file: {e}")

    def process_file(self):
        try:
            subprocess.run(["python", "./listmode.py", self.json_file, '--output', self.csv_file, self.temp_dir, self.temp_dir], check=True)
            messagebox.showinfo("Success", f"File processed successfully. Output: {self.csv_file}")
            self.show_images()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Processing Error", f"Failed to process file: {e}")

    def show_images(self):
        self.tif_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.tif')]
        if not self.tif_files:
            messagebox.showinfo("No Images", "No .tif files found in the directory!")
            return

        self.current_image_index = 0
        self.display_image(self.tif_files[self.current_image_index])
        self.metadata_ui.update_navigation_buttons(self.current_image_index, len(self.tif_files))
        self.metadata_ui.show()  # Show the metadata window

    def display_image(self, image_file):
        image_path = os.path.join(self.temp_dir, image_file)
        img = Image.open(image_path)
        img = img.resize((400, 400), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)

        if self.image_label is None:
            self.image_label = tk.Label(self.root, image=img_tk)
            self.image_label.image = img_tk
            self.image_label.pack(pady=10)
        else:
            self.image_label.config(image=img_tk)
            self.image_label.image = img_tk

        # Load saved metadata if it exists
        metadata = self.metadata_handler.load_metadata(image_file)  # Load metadata for the current image
        self.metadata_ui.display_metadata(image_file, metadata)  # Pass to UI for display

    def save_metadata_callback(self):
        image_file = self.tif_files[self.current_image_index]
        biological = self.metadata_ui.biological_entry.get()
        species = self.metadata_ui.species_entry.get()
        self.metadata_handler.save_metadata(image_file, biological, species)

if __name__ == "__main__":
    root = tk.Tk()
    app = BlobApp(root)
    root.mainloop()
