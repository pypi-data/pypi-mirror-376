from mimetypes import guess_type

GUESSES = {"image/jpeg": ("jpg", "jpeg"), "image/png": ("png",)}


def mime_for(path: str, contents: bytes) -> str | None:
    mime, *_ = guess_type(path)
    if isinstance(mime, str):
        return mime

    for mime, guesses in GUESSES.items():
        for guess in guesses:
            if guess.upper().encode() in contents[:128]:
                return mime
            if guess.encode() in contents[:128]:
                return mime

    return None
