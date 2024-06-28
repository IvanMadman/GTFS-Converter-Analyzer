import tkinter as tk
from ui import App, stop_flask_server
import atexit

# Function to clean up resources on exit
def cleanup():
    stop_flask_server()
atexit.register(cleanup)
def main():
    root = tk.Tk()
    app = App(root)
    
    root.mainloop()
    # Register cleanup function to be called on exit
    
if __name__ == "__main__":
    main()








