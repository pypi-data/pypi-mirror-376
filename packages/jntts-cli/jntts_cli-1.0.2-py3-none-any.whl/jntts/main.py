import sys
import os
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# from .config import CACHE_DIR
from .tts_utils import load_models
from .box_voice import run_boxvoice
from .file_tts import run_file_tts
from .hardware_check import run_hardware_check
from .ui import display_main_menu
from .about import show_about
from appdirs import user_data_dir

APP_NAME = "jntts"
APP_AUTHOR = "JustinNguyen" 
USER_DATA_PATH = user_data_dir(APP_NAME, APP_AUTHOR)

INPUT_DIR = os.path.join(USER_DATA_PATH, "Input")
OUTPUT_DIR = os.path.join(USER_DATA_PATH, "Output")
CACHE_DIR_APP = os.path.join(USER_DATA_PATH, "audio_cache")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def setup_directories():
    print(f"Dữ liệu ứng dụng sẽ được lưu tại: {USER_DATA_PATH}")
    print("Đang kiểm tra và tạo các thư mục cần thiết...")
    
    required_dirs = [INPUT_DIR, OUTPUT_DIR, CACHE_DIR_APP]
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f" -> Đã tạo thư mục: {dir_name}")
    print("Gợi ý: Hãy đặt các file .txt của bạn vào thư mục 'Input' ở trên.")

def main():
    setup_directories()
    
    model, processor, device, sampling_rate = load_models()

    try:
        while True:
            display_main_menu()
            
            choice = input("Nhập lựa chọn của bạn (0-4): ")

            if choice == '1':
                run_boxvoice(model, processor, device, sampling_rate, CACHE_DIR_APP)
            elif choice == '2':
                run_file_tts(model, processor, device, sampling_rate, INPUT_DIR, OUTPUT_DIR)
            elif choice == '3':
                run_hardware_check()
            elif choice == '4':
                show_about()
            elif choice == '0':
                print("Tạm biệt!")
                sys.exit(0)
            else:
                print("Lựa chọn không hợp lệ. Vui lòng thử lại.")
                input("Nhấn Enter để tiếp tục...")

    except KeyboardInterrupt:
        print("\n\nĐã thoát chương trình. Tạm biệt!")
        sys.exit(0)

if __name__ == "__main__":
    main()