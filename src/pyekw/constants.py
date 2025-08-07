"""
Constants used in eKW number processing.
"""

# Character values for check digit calculation
CHARACTER_VALUES = {
    "0": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "A": 11,
    "B": 12,
    "C": 13,
    "D": 14,
    "E": 15,
    "F": 16,
    "G": 17,
    "H": 18,
    "I": 19,
    "J": 20,
    "K": 21,
    "L": 22,
    "M": 23,
    "N": 24,
    "O": 25,
    "P": 26,
    "R": 27,
    "S": 28,
    "T": 29,
    "U": 30,
    "W": 31,
    "Y": 32,
    "Z": 33,
    "X": 10,
}

# Weights for check digit calculation (repeating pattern: 1, 3, 7)
WEIGHTS = [1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7]

# KW number format constants
KW_PARTS_COUNT = 3
COURT_CODE_MAX_LENGTH = 4
REGISTER_NUMBER_LENGTH = 8
CHECK_DIGIT_LENGTH = 1
