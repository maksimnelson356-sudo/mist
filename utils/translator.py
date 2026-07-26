import json
import os

LOCALES = {}
_current_lang = "ru"


def load_locale(lang: str) -> dict:
    if lang in LOCALES:
        return LOCALES[lang]

    path = os.path.join(os.path.dirname(__file__), "..", "locale", f"{lang}.json")
    if not os.path.exists(path):
        return {}

    with open(path, encoding="utf-8") as f:
        LOCALES[lang] = json.load(f)
    return LOCALES[lang]


def set_language(lang: str):
    global _current_lang
    _current_lang = lang


def t(key: str, **kwargs) -> str:
    strings = load_locale(_current_lang)
    template = strings.get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template
