from string import ascii_lowercase, digits


def canonicalize(key: str) -> str:
    return ''.join([c for c in key.lower() if c in ascii_lowercase + digits + '@'])
