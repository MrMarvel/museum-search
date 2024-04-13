import main as app_main
from utils import remove_trash


def main():
    choose = input(f'Remove trash in {app_main.UPLOAD_FOLDER} folder? y/n ')
    if choose.lower() == 'y':
        remove_trash()


if __name__ == '__main__':
    main()
