from validators import url


def validate_url(input_url):
    if len(input_url) > 255:
        return False, 'URL превышает 255 символов'
    if not url(input_url):
        return False, 'Некорректный URL'
    return True, ''
