from enum import Enum

class GamePhase(str, Enum):
    """Фазы игры для использования в session и narrator."""
    WAITING = "waiting"
    PRE_GAME = "pre_game"
    DAY = "day"
    NOMINATION = "nomination"
    DEFENSE = "defense"
    VOTING = "voting"
    DEFENSE_TIE = "defense_tie"
    VOTING_TIE = "voting_tie"
    NIGHT_MAFIA = "night_mafia"
    NIGHT_DON = "night_don"
    NIGHT_SHERIFF = "night_sheriff"
    NIGHT_DOCTOR = "night_doctor"
    LAST_WORDS = "last_words"
    GAME_OVER = "game_over"

# Описание фаз для ведущего (можно расширить)
PHASE_DESCRIPTIONS = {
    GamePhase.WAITING: "Ожидание игроков в лобби",
    GamePhase.PRE_GAME: "30 обратного отсчёта готовности перед началом игры",
    GamePhase.DAY: "Дневное обсуждение, игроки говорят по очереди",
    GamePhase.NOMINATION: "Дополнительное время на выдвижение кандидата",
    GamePhase.DEFENSE: "Речь защиты выставленных игроков",
    GamePhase.VOTING: "Голосование за исключение",
    GamePhase.DEFENSE_TIE: "Повторная защита при ничье",
    GamePhase.VOTING_TIE: "Повторное голосование при ничье",
    GamePhase.NIGHT_MAFIA: "Ночь: мафия выбирает жертву",
    GamePhase.NIGHT_DON: "Ночь: дон проверяет игрока",
    GamePhase.NIGHT_SHERIFF: "Ночь: шериф проверяет игрока",
    GamePhase.NIGHT_DOCTOR: "Ночь: доктор лечит игрока",
    GamePhase.LAST_WORDS: "Прощальная минута перед смертью",
    GamePhase.GAME_OVER: "Игра завершена",
}