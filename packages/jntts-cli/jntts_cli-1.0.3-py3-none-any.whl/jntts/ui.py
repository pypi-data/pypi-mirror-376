import os
import pyfiglet

VERSION = "v1.0.3 - Developed By Justin Nguyen 🇻🇳"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def generate_centered_ascii_title(text, font='standard'):
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80

    fig = pyfiglet.Figlet(font=font, width=terminal_width)
    banner_text = fig.renderText(text)
    
    lines = banner_text.splitlines()
    centered_lines = [line.center(terminal_width) for line in lines]
    centered_banner = "\n".join(centered_lines)

    return centered_banner

def display_main_menu():
    clear_screen()
    
    print(generate_centered_ascii_title("TOOL TEXT TO SPEECH"))
    
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80
        
    print(f"{VERSION.center(terminal_width)}")
    print("\n" + "=" * terminal_width)
    print("\n1. Nghe thử giọng nói (Box Voice)")
    print("\n2. Tạo giọng nói (Text To Speech)")
    print("\n3. Kiểm tra phần cứng (Check CPU/GPU)")
    print("\n4. Thông tin & Tác giả (About)")
    print("\n0. Thoát chương trình (Exit)")
    print("\n" + "=" * terminal_width)