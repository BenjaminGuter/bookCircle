def is_visible(post_chapter: int, reader_chapter: int) -> bool:
    """Ein Beitrag ist sichtbar, wenn der Leser mindestens so weit ist wie der Beitrag."""
    return reader_chapter >= post_chapter