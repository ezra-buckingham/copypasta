import pyautogui
import time
import click
from pathlib import Path

DEFAULT_SLEEP = 5.0

# variables to control actions
configured_sleep = DEFAULT_SLEEP
content = ""


def send_keystrokes():
    # Give user time to click on text field to activate
    time.sleep(configured_sleep)
    
    try:
        # Write content to text field
        pyautogui.typewrite(content)
        
        return True
    except:
        return False

@click.group()
def main():
    pass


@main.command()
@click.option("-s", "--sleep", type=float, default=DEFAULT_SLEEP, help="""
    Sleep time before typing content
""")
@click.option("-f", "--file", type=Path, help="""
    File to write out as text
""")
def cli(sleep, file):
    """ CLI for typing a file out """
    global configured_sleep
    global content
    
    configured_sleep = sleep
    
    file = Path(file)
    content = file.read_text()
    
    send_keystrokes()
    

@main.command()
def ui():
    """ Display a UI for pasting in text """
    import customtkinter
    
    # Define the application
    app = customtkinter.CTk()
    app.geometry("500x500")
    app.title("CopyPasta Send Keys")

    # The callback function to set sleep time
    def slider_callback(value):
        global configured_sleep
        label_1.configure(text=f"Sleep Time: { value }s")
        configured_sleep = value
        
    # The callback function to send the keys
    def button_callback():
        global send_keystrokes
        global content
        
        content = text_1.get()
        event = send_keystrokes()
    
        if event: app.destroy()

    # Define the frame
    frame_1 = customtkinter.CTkFrame(master=app)
    frame_1.pack(pady=20, padx=20, fill="both", expand=True)

    # Define the textbox for user input
    text1_font = customtkinter.CTkFont(family="courier", size=14, weight="bold")
    text_1 = customtkinter.CTkEntry(master=frame_1, font=text1_font, placeholder_text="Text here...", width=450, height=100)
    text_1.pack(pady=10, padx=10)

    # Create the label for the sleep time
    label_1 = customtkinter.CTkLabel(master=frame_1, text=f"Sleep Time: { DEFAULT_SLEEP }s")
    label_1.pack(pady=10, padx=10)

    # Create the slider for the sleep time
    slider_1 = customtkinter.CTkSlider(master=frame_1, command=slider_callback, from_=0, to=25, number_of_steps=25)
    slider_1.pack(pady=10, padx=10)
    slider_1.set(DEFAULT_SLEEP)

    # Create the send button
    button_1 = customtkinter.CTkButton(master=frame_1, text="Send Keys", command=button_callback)
    button_1.pack(pady=10, padx=10)

    # Run this thanggg
    app.mainloop()


if __name__ == "__main__":
    main()