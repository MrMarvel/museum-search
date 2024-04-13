from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


confirm_buttons = [
    [InlineKeyboardButton(text="◀️ Назад", callback_data="input_image"),
    InlineKeyboardButton(text="⚙️ Обработка", callback_data="process")],
]

back_buttons = [
    [InlineKeyboardButton(text="◀️ Меню", callback_data="menu"),],
]

start_buttons = [
    [InlineKeyboardButton(text="ℹ️", callback_data="get_help"),
     InlineKeyboardButton(text="🖼️ Обработать изображение", callback_data="input_image")],
]

help_buttons = [
    [InlineKeyboardButton(text="Start", callback_data="menu"),],
]
confirm_menu = InlineKeyboardMarkup(inline_keyboard=confirm_buttons)
start_menu = InlineKeyboardMarkup(inline_keyboard=start_buttons)
back_menu = InlineKeyboardMarkup(inline_keyboard=back_buttons)
help_menu = InlineKeyboardMarkup(inline_keyboard=help_buttons)