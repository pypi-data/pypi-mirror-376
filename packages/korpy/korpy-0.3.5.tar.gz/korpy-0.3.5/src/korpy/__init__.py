"""
a package for korean texts
"""

from .core import vowels, consonants, extend, combine, group, finals, is_korean, get_sound, from_sound, words, to_korean, from_korean, to_int, from_int, korean_ratio, fully_korean, PERCENTAGE, PERCENTAGE_UNTIL_1, PERCENTAGE_UNTIL_2, from_datetime, to_datetime, similarity, accuracy_per_word, fix_spelling
from .games import ConcludingRemarksGame, ConcludingRemarksRobot, ConsonantQuiz, ConsonantQuizRobot

__all__ = ["vowels", "consonants", "extend", "combine", "group", "finals", "is_korean", "get_sound", "from_sound", "words", "to_korean", "from_korean", "to_int", "from_int", "korean_ratio", "fully_korean", "PERCENTAGE", "PERCENTAGE_UNTIL_1", "PERCENTAGE_UNTIL_2", "from_datetime", "to_datetime", "similarity", "accuracy_per_word", "fix_spelling", "ConcludingRemarksGame", "ConcludingRemarksRobot", "ConsonantQuiz", "ConsonantQuizRobot"]