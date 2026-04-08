import random

SFX_MAP = {
    "धम": ["sfx/boom1.mp3", "sfx/boom2.mp3"],
    "ठक": ["sfx/knock1.mp3"],
    "फुफकार": ["sfx/hiss1.mp3"],
    "हँसी": ["sfx/laugh1.mp3"],
}

def get_sfx_file(keyword: str):
    keyword = keyword.strip().replace("!", "")
    files = SFX_MAP.get(keyword, [])
    return random.choice(files) if files else None