from enum import Enum

class Role(str, Enum):
    MAFIA = "mafia"
    DON = "don"
    SHERIFF = "sheriff"
    DOCTOR = "doctor"
    CIVILIAN = "civilian"