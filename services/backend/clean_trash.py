import main as app_main


def remove_trash():
    l = app_main.find_trash_items()
    for trash in l:
        trash.unlink()


def main():
    choose = input(f'Remove trash in {app_main.UPLOAD_FOLDER} folder? y/n ')
    if choose.lower() == 'y':
        remove_trash()


if __name__ == '__main__':
    main()
