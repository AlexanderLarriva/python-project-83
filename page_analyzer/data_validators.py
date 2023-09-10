from validators import url


def validate_url(input_url):
    # Проверяем длинну введеного адреса
    if len(input_url) > 255:
        return False, 'URL превышает 255 символов'
    # Проверяем корректность введеного url
    if not url(input_url):
        return False, 'Некорректный URL'
    return True, ''
