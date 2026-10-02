import os
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters


# =========================
# РУССКИЙ ЛИТЕРАТУРНЫЙ БРАЙЛЬ
# =========================

RUSSIAN_TO_BRAILLE = {
    "а": "⠁",
    "б": "⠃",
    "в": "⠺",
    "г": "⠛",
    "д": "⠙",
    "е": "⠑",
    "ё": "⠡",
    "ж": "⠚",
    "з": "⠵",
    "и": "⠊",
    "й": "⠯",
    "к": "⠅",
    "л": "⠇",
    "м": "⠍",
    "н": "⠝",
    "о": "⠕",
    "п": "⠏",
    "р": "⠗",
    "с": "⠎",
    "т": "⠞",
    "у": "⠥",
    "ф": "⠋",
    "х": "⠓",
    "ц": "⠉",
    "ч": "⠟",
    "ш": "⠱",
    "щ": "⠭",
    "ъ": "⠷",
    "ы": "⠮",
    "ь": "⠾",
    "э": "⠪",
    "ю": "⠳",
    "я": "⠫",
}

# Заглавная буква
CAPITAL_SIGN = "⠠"

# Цифровой знак
NUMBER_SIGN = "⠼"

# Цифры в Брайле соответствуют буквам а-й
DIGITS_TO_BRAILLE = {
    "1": "⠁",
    "2": "⠃",
    "3": "⠉",
    "4": "⠙",
    "5": "⠑",
    "6": "⠋",
    "7": "⠛",
    "8": "⠓",
    "9": "⠊",
    "0": "⠚",
}

BRAILLE_TO_DIGITS = {v: k for k, v in DIGITS_TO_BRAILLE.items()}

# Основные знаки препинания
PUNCTUATION_TO_BRAILLE = {
    ",": "⠂",
    ";": "⠆",
    ":": "⠒",
    ".": "⠲",
    "!": "⠖",
    "?": "⠦",
    "-": "⠤",
    "—": "⠠⠤",
    "(": "⠐⠣",
    ")": "⠐⠜",
    "\"": "⠦",
    "'": "⠄",
}

BRAILLE_TO_PUNCTUATION = {
    "⠂": ",",
    "⠆": ";",
    "⠒": ":",
    "⠲": ".",
    "⠖": "!",
    "⠦": "?",
    "⠤": "-",
    "⠠⠤": "—",
    "⠐⠣": "(",
    "⠐⠜": ")",
    "⠄": "'",
}


def russian_to_braille(text: str) -> str:
    result = []
    previous_was_number = False

    for char in text:
        lower_char = char.lower()

        # Цифры
        if char in DIGITS_TO_BRAILLE:
            if not previous_was_number:
                result.append(NUMBER_SIGN)
            result.append(DIGITS_TO_BRAILLE[char])
            previous_was_number = True
            continue

        # После цифры пробел/знак заканчивает числовой режим
        if previous_was_number:
            previous_was_number = False

        # Русские буквы
        if lower_char in RUSSIAN_TO_BRAILLE:
            if char.isupper():
                result.append(CAPITAL_SIGN)

            result.append(RUSSIAN_TO_BRAILLE[lower_char])
            continue

        # Знаки препинания
        if char in PUNCTUATION_TO_BRAILLE:
            result.append(PUNCTUATION_TO_BRAILLE[char])
            continue

        # Пробелы, переносы строк и неизвестные символы
        result.append(char)

    return "".join(result)


def braille_to_russian(text: str) -> str:
    braille_to_russian_map = {
        value: key for key, value in RUSSIAN_TO_BRAILLE.items()
    }

    result = []
    i = 0
    capital_next = False
    number_mode = False

    while i < len(text):
        char = text[i]

        # Заглавная буква
        if char == CAPITAL_SIGN:
            capital_next = True
            i += 1
            continue

        # Числовой знак
        if char == NUMBER_SIGN:
            number_mode = True
            i += 1
            continue

        # Пробел / перенос строки
        if char.isspace():
            result.append(char)
            number_mode = False
            capital_next = False
            i += 1
            continue

        # Составной знак длинного тире
        if text[i:i + 2] == "⠠⠤":
            result.append("—")
            i += 2
            continue

        # Составные скобки
        if text[i:i + 2] == "⠐⠣":
            result.append("(")
            i += 2
            continue

        if text[i:i + 2] == "⠐⠜":
            result.append(")")
            i += 2
            continue

        # Цифры
        if number_mode and char in BRAILLE_TO_DIGITS:
            result.append(BRAILLE_TO_DIGITS[char])
            i += 1
            continue

        # Если встретили обычный знак после числа
        number_mode = False

        # Пунктуация
        if char in BRAILLE_TO_PUNCTUATION:
            result.append(BRAILLE_TO_PUNCTUATION[char])
            i += 1
            continue

        # Русская буква
        if char in braille_to_russian_map:
            letter = braille_to_russian_map[char]

            if capital_next:
                letter = letter.upper()
                capital_next = False

            result.append(letter)
            i += 1
            continue

        # Неизвестный символ оставляем как есть
        result.append(char)
        i += 1

    return "".join(result)


def looks_like_braille(text: str) -> bool:
    """
    Определяем направление перевода.
    Если в сообщении есть символы Unicode Braille Patterns,
    считаем его текстом Брайля.
    """
    braille_characters = [
        char for char in text
        if "\u2800" <= char <= "\u28ff"
    ]

    return len(braille_characters) > 0


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message or not update.message.text:
        return

    text = update.message.text

    if looks_like_braille(text):
        result = braille_to_russian(text)
    else:
        result = russian_to_braille(text)

    await update.message.reply_text(result)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отправь русский текст — я переведу его в Брайль.\n\n"
        "Отправь символы Брайля — переведу их обратно в русский текст."
    )


def main():
    token = os.environ.get("BOT_TOKEN")

    if not token:
        raise RuntimeError("Не найден BOT_TOKEN")

    app = Application.builder().token(token).build()

    app.add_handler(
        MessageHandler(filters.COMMAND, start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("Бот запущен.")

    app.run_polling()


if __name__ == "__main__":
    main()
