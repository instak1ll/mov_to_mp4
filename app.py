import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import re

class MOVtoMP4ConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("MOV to MP4 Converter")
        master.geometry("600x350")
        master.resizable(False, False)

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", font=("Helvetica", 10), padding=8)
        self.style.configure("TLabel", font=("Helvetica", 10), padding=5)
        self.style.configure("TEntry", font=("Helvetica", 10), padding=5)

        self.input_file_path = tk.StringVar()
        self.output_dir_path = tk.StringVar()
        self.total_duration_seconds = 0
        self.progress_percentage_text = tk.StringVar()

        main_frame = ttk.Frame(master, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=3)
        main_frame.columnconfigure(2, weight=1)

        ttk.Label(main_frame, text="Input MOV File:").grid(row=0, column=0, sticky="w", pady=5)
        self.input_entry = ttk.Entry(main_frame, textvariable=self.input_file_path, width=50)
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(main_frame, text="Browse...", command=self.browse_input_file).grid(row=0, column=2, sticky="ew", pady=5)

        ttk.Label(main_frame, text="Output MP4 Folder:").grid(row=1, column=0, sticky="w", pady=5)
        self.output_entry = ttk.Entry(main_frame, textvariable=self.output_dir_path, width=50)
        self.output_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(main_frame, text="Select Folder...", command=self.browse_output_dir).grid(row=1, column=2, sticky="ew", pady=5)

        self.action_container_frame = ttk.Frame(main_frame)
        self.action_container_frame.grid(row=2, column=0, columnspan=3, pady=20, sticky="ew")
        self.action_container_frame.columnconfigure(0, weight=1)

        self.convert_button = ttk.Button(self.action_container_frame, text="Convert MOV to MP4", command=self.start_conversion_thread)
        self.convert_button.pack(fill=tk.X, expand=True)

        self.progress_percentage_label = ttk.Label(self.action_container_frame, textvariable=self.progress_percentage_text, foreground="#DAA520")
        self.progress_bar = ttk.Progressbar(self.action_container_frame, orient="horizontal", mode="determinate")

        self.general_status_label = ttk.Label(main_frame, text="Ready.", foreground="blue")
        self.general_status_label.grid(row=3, column=0, columnspan=3, pady=5, sticky="w")

        self.output_dir_path.set(os.path.expanduser("~/Desktop"))

    def set_general_status(self, message, color="blue"):
        self.general_status_label.config(text=message, foreground=color)
        self.master.update_idletasks()

    def update_progress_ui(self, percentage):
        self.progress_bar['value'] = percentage
        self.progress_percentage_text.set(f"{percentage:.1f}% completed")
        self.master.update_idletasks()

    def browse_input_file(self):
        file_selected = filedialog.askopenfilename(
            title="Select MOV File",
            filetypes=[("MOV Video Files", "*.mov"), ("All Files", "*.*")]
        )
        if file_selected:
            self.input_file_path.set(file_selected)
            self.set_general_status("Input file selected.")
            self.progress_percentage_text.set("0.0% completed")
            self.progress_bar.set(0)

    def browse_output_dir(self):
        dir_selected = filedialog.askdirectory(
            title="Select Output Folder for MP4"
        )
        if dir_selected:
            self.output_dir_path.set(dir_selected)
            self.set_general_status("Output folder selected.")

    def get_video_duration(self, video_path):
        try:
            command = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            result = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            duration_str = result.stdout.strip()
            return float(duration_str)
        except FileNotFoundError:
            self.master.after(0, lambda: messagebox.showerror("Error", "FFprobe not found. Please ensure FFmpeg (which includes ffprobe) is installed and in your system PATH."))
            return 0
        except subprocess.CalledProcessError as e:
            self.master.after(0, lambda: messagebox.showerror("FFprobe Error", f"Could not get video duration with FFprobe:\n{e.stderr.strip()}"))
            return 0
        except ValueError:
            self.master.after(0, lambda: messagebox.showerror("FFprobe Error", "Could not parse video duration from FFprobe output."))
            return 0
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Error", f"An unexpected error occurred while getting video duration: {e}"))
            return 0

    def start_conversion_thread(self):
        input_path = self.input_file_path.get()
        output_dir = self.output_dir_path.get()

        if not input_path:
            messagebox.showwarning("Input Error", "Please select an input MOV file.")
            return
        if not output_dir:
            messagebox.showwarning("Output Error", "Please select an output folder for the MP4.")
            return

        self.convert_button.pack_forget()
        self.progress_percentage_label.pack(pady=(0,5))
        self.progress_bar.pack(fill=tk.X, expand=True)

        self.set_general_status("Starting conversion...", "#DAA520")
        self.progress_percentage_text.set("0.0% completed")
        self.progress_bar.config(mode="determinate", value=0)

        conversion_thread = threading.Thread(target=self.perform_conversion, args=(input_path, output_dir))
        conversion_thread.start()

    def perform_conversion(self, input_path, output_dir):
        try:
            self.total_duration_seconds = self.get_video_duration(input_path)
            if self.total_duration_seconds == 0:
                self.set_general_status("Could not get video duration. Conversion might proceed without precise progress updates.", "red")
                self.master.after(0, lambda: self.progress_bar.config(mode="indeterminate"))
                self.master.after(0, lambda: self.progress_bar.start(10))

            base_name = os.path.basename(input_path)
            output_filename = os.path.splitext(base_name)[0] + '.mp4'
            output_file_path = os.path.join(output_dir, output_filename)

            command = [
                'ffmpeg',
                '-i', input_path,
                '-f', 'mp4',
                '-y',
                output_file_path
            ]
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            for line in iter(process.stderr.readline, ''):
                match = re.search(r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})', line)
                if match:
                    hours = int(match.group(1))
                    minutes = int(match.group(2))
                    seconds = int(match.group(3))
                    milliseconds = int(match.group(4)) * 10

                    current_time_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0

                    if self.total_duration_seconds > 0:
                        percentage = (current_time_seconds / self.total_duration_seconds) * 100
                        if percentage > 100:
                            percentage = 100
                        self.master.after(0, self.update_progress_ui, percentage)
                    else:
                        self.master.after(0, lambda: self.progress_bar.step(0.5))

            process.wait()

            if process.returncode == 0:
                self.master.after(0, self.update_progress_ui, 100)
                self.set_general_status(f"Conversion successful: '{output_filename}' saved to '{output_dir}'.", "green")
                messagebox.showinfo("Success", f"File converted:\n{output_filename}\nSaved to:\n{output_dir}")
            else:
                error_message = process.stderr.read().strip()
                self.set_general_status(f"ERROR during conversion: {error_message}", "red")
                messagebox.showerror("Conversion Error", f"An error occurred during conversion:\n{error_message}")

        except FileNotFoundError:
            self.set_general_status("ERROR: FFmpeg not found. Ensure it's installed and in your PATH.", "red")
            messagebox.showerror("Error", "FFmpeg not found in system PATH.\nPlease ensure it's installed and its executables are accessible.")
        except Exception as e:
            self.set_general_status(f"UNEXPECTED ERROR: {e}", "red")
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}")
        finally:
            self.progress_percentage_label.pack_forget()
            self.progress_bar.pack_forget()
            self.convert_button.pack(fill=tk.X, expand=True)

            self.convert_button.config(state=tk.NORMAL)
            self.progress_bar.stop()
            self.progress_bar.config(mode="determinate", value=0)
            self.set_general_status("Ready.", "blue")

if __name__ == "__main__":
    root = tk.Tk()
    app = MOVtoMP4ConverterApp(root)
    root.mainloop()
