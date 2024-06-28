import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from gtfs_processor import process_gtfs_file
import threading
import os
import subprocess
import webbrowser
import time
import requests

flask_process = None

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("GTFS Traffic Analysis")
        self.root.geometry("600x400")
        self.root.configure(bg="#f0f0f0")
        
        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', font=('Helvetica', 12), padding=10, background="#4CAF50", foreground="white")
        self.style.map('TButton', background=[('active', '#45a049')])
        self.style.configure('TLabel', font=('Helvetica', 10), background="#f0f0f0")
        self.style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'), background="#f0f0f0")
        self.style.configure('TProgressbar', thickness=8, troughcolor='#f0f0f0', background="#4CAF50")

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20 20 20 20", style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_label = ttk.Label(main_frame, text="GTFS Traffic Analysis", style='Header.TLabel')
        header_label.pack(pady=(0, 20))

        self.create_upload_section(main_frame, "Upload GTFS Zip", self.upload_gtfs_file,
                                   "Choose a GTFS zip file to be uploaded and converted into a database")
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate', style='TProgressbar')
        self.progress = tk.StringVar()
        self.progress_label = ttk.Label(main_frame, textvariable=self.progress, style='TLabel')
        
        self.separator = ttk.Separator(main_frame, orient='horizontal')
        self.separator.pack(fill='x', pady=20)
        
        self.create_upload_section(main_frame, "Upload Database", self.upload_db_file,
                                   "Choose any GTFS database supporting SQL, it SHOULD work even with DBs not converted from here")

    def create_upload_section(self, parent, button_text, command, label_text):
        frame = ttk.Frame(parent, style='TFrame')
        frame.pack(fill='x', pady=10)

        button = ttk.Button(frame, text=button_text, command=command)
        button.pack(side='left', padx=(0, 10))

        label = ttk.Label(frame, text=label_text, wraplength=300, justify="left", style='TLabel')
        label.pack(side='left', fill='x', expand=True)

    def show_progress_bar(self):
        self.progress_bar.pack(pady=10, before=self.separator)
        self.progress_label.pack(pady=5, before=self.separator)
        self.progress_bar.start()

    def hide_progress_bar(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()

    def upload_gtfs_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Zip files", "*.zip")])
        if file_path:
            self.show_progress_bar()
            threading.Thread(target=self.process_gtfs_file, args=(file_path,)).start()

    def process_gtfs_file(self, file_path):
        try:
            process_gtfs_file(file_path, self.update_progress)
            messagebox.showinfo("Success", "GTFS data processed successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.hide_progress_bar()


    @staticmethod
    def is_flask_server_running(url='http://127.0.0.1:5000'):
            try:
                response = requests.get(url)
                return response.status_code == 200
            except requests.ConnectionError:
                return False



    def start_flask_server(self, db_path):
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        print(f"Setting DATABASE_URL to sqlite:///{db_path}")
    
        if self.is_flask_server_running():
            print("Flask server is already running. Reloading...")
            # Send a request to the server to reload the database
            # Assuming you have an endpoint to reload the configuration
            try:
                response = requests.post('http://127.0.0.1:5000/reload', json={'db_path': db_path})
                if response.status_code == 200:
                    print("Server reloaded with new database successfully.")
                else:
                    print(f"Failed to reload server: {response.status_code}")
            except requests.ConnectionError:
                print("Error connecting to the server for reload.")
        else:
            print("Starting Flask server...")
            global flask_process
            flask_process = subprocess.Popen(['python', 'server.py'])

    

    def upload_db_file(self):
            db_path = filedialog.askopenfilename(filetypes=[("Database files", "*.db")])
            if db_path:
                thread = threading.Thread(target=self.start_flask_server, args=(db_path,))
                thread.start()
                # Wait for the Flask server to start
                time.sleep(3)
            # Assuming the Flask server runs on localhost and port 5000
                webbrowser.open("http://127.0.0.1:5000")

    def update_progress(self, percentage):
        self.progress.set(f"Progress: {percentage}%")


def stop_flask_server():
        global flask_process
        if flask_process:
            flask_process.terminate()
            flask_process.wait()