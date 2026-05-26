# server/game/session.py

import asyncio
import logging
import random
from enum import Enum
from typing import Optional

from server.game.player import Player
from server.game.roles import Role
from server.game.constants import *

logger = logging.getLogger(__name__)


class GamePhase(str, Enum):
    WAITING = "waiting"
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


class DefaultNarrator:
    """Заглушка рассказчика, пока не подключён AI-ведущий."""
    async def day_start(self, day_number: int) -> str:
        return f"Город просыпается. День {day_number}."

    async def night_start(self) -> str:
        return "Город засыпает."

    async def kill_announcement(self, username: str) -> str:
        return f"Сегодня ночью убит {username}."

    async def peaceful_night(self) -> str:
        return "Ночь прошла спокойно, никто не умер."

    async def player_speech(self, username: str, duration: int) -> str:
        return f"Слово предоставляется {username}. ({duration} сек)"

    async def nomination_extra(self, username: str) -> str:
        return f"{username}, у вас 15 секунд для выставления кандидата (без речи)."

    async def defense_speech(self, username: str, duration: int) -> str:
        return f"Оправдательное слово игрока {username} ({duration} сек)."

    async def voting_start(self, duration: int) -> str:
        return f"Голосование ({duration} сек). Отправьте !vote <ник>."

    async def tie_defense(self, names: str, duration: int) -> str:
        return f"Ничья. Дополнительное слово для: {names} ({duration} сек)."

    async def player_eliminated(self, username: str) -> str:
        return f"{username} покидает игру."

    async def mafia_chat_opened(self) -> str:
        return "Мафия просыпается (чат открыт 60 сек)."

    async def mafia_chat_closed(self) -> str:
        return "Чат мафии закрыт. У вас есть 15 секунд для выбора цели (без чата)."

    async def don_check(self) -> str:
        return "Дон просыпается и делает проверку (30 сек)."

    async def sheriff_check(self) -> str:
        return "Шериф просыпается и делает проверку (30 сек)."

    async def doctor_heal(self) -> str:
        return "Доктор просыпается и лечит (30 сек)."


class GameSession:
    def __init__(self, game_id: str, test_mode: bool = False, narrator: Optional[DefaultNarrator] = None):
        self.game_id = game_id
        self.players: dict[str, Player] = {}
        self.phase = GamePhase.WAITING
        self.test_mode = test_mode
        self.narrator = narrator or DefaultNarrator()

        # Таймеры
        self._phase_timer_task: Optional[asyncio.Task] = None
        self._speech_timer_task: Optional[asyncio.Task] = None
        self._nomination_timer_task: Optional[asyncio.Task] = None
        self._last_words_timer_task: Optional[asyncio.Task] = None

        # Порядок выступлений днём
        self._speaker_order: list[str] = []          # user_id живых в порядке очереди
        self._current_speaker_index = 0
        self._current_speaker_id: Optional[str] = None
        self._player_nominated_during_speech = False
        self._speaker_nominated_target: Optional[str] = None  # кого выставил текущий оратор
        self._day_number = 0
        self.is_first_day = True                      # первый день – без номинаций

        # Голосование
        self.nominated_players: list[str] = []        # user_id выставленных на текущее голосование
        self.votes: dict[str, str] = {}               # voter_id -> target_id
        self.voting_targets: list[str] = []           # допустимые цели голосования
        self._defense_queue: list[str] = []           # очередь оправдывающихся
        self._current_defense_index = 0
        self._vote_change_counts: dict[str, int] = {} # счётчик смен голоса

        # Ночные действия
        self.mafia_target: Optional[str] = None
        self.don_check_target: Optional[str] = None
        self.sheriff_check_target: Optional[str] = None
        self.doctor_heal_target: Optional[str] = None
        self._mafia_votes: dict[str, str] = {}        # user_id -> target_id (голоса мафии)

        # Дон (без передачи привилегии)
        self.don_user_id: Optional[str] = None
        self._don_found_sheriff = False               # нашёл ли дон шерифа
        self._don_checked: set[str] = set()           # проверенные доном цели
        self._sheriff_checked: set[str] = set()       # проверенные шерифом
        self._last_heal_target: Optional[str] = None   # кого лечил доктор в прошлую ночь

        self._mafia_chat_enabled = False

        # Логи для мёртвых
        self.dead_chat_log: list[dict] = []           # история общего чата и системных событий
        self.mafia_chat_log: list[dict] = []          # история чата мафии (для умерших мафиози)

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------
    def _find_player_by_username(self, username: str) -> Optional[Player]:
        for p in self.players.values():
            if p.username == username:
                return p
        return None

    async def _change_phase(self, new_phase: GamePhase):
        self.phase = new_phase
        logger.info("Game %s phase -> %s", self.game_id, new_phase)

    async def _start_timer(self, seconds: float, callback, attr: str = '_phase_timer_task'):
        """Запускает таймер, отменяя предыдущий (по указанному атрибуту)."""
        task_attr = getattr(self, attr, None)
        if task_attr and not task_attr.done():
            task_attr.cancel()
        async def _wait_and_call():
            await asyncio.sleep(seconds)
            await callback()
        setattr(self, attr, asyncio.create_task(_wait_and_call()))

    async def cancel_timers(self):
        """Отменяет все активные таймеры."""
        for task in [self._phase_timer_task, self._speech_timer_task, self._nomination_timer_task, self._last_words_timer_task]:
            if task and not task.done():
                task.cancel()
        self._phase_timer_task = None
        self._speech_timer_task = None
        self._nomination_timer_task = None
        self._last_words_timer_task = None

    async def _imitate_pause(self):
        """Случайная пауза для отсутствующей роли."""
        pause = random.uniform(5, 30)
        await asyncio.sleep(pause)

    # ------------------------------------------------------------------
    # Инициализация и старт игры
    # ------------------------------------------------------------------
    def add_player(self, user_id: str, username: str) -> Player:
        if user_id in self.players:
            raise ValueError("Игрок уже в игре")
        player = Player(user_id, username)
        self.players[user_id] = player
        return player

    def assign_roles(self):
        n = len(self.players)
        if n < MIN_PLAYERS or n > MAX_PLAYERS:
            raise ValueError("Недопустимое количество игроков")

        roles_pool = []
        if n == 6:
            roles_pool = [Role.DON, Role.MAFIA, Role.SHERIFF, Role.DOCTOR, Role.CIVILIAN, Role.CIVILIAN]
        elif n == 7:
            roles_pool = [Role.DON, Role.MAFIA, Role.SHERIFF, Role.DOCTOR] + [Role.CIVILIAN] * 3
        elif n == 8:
            roles_pool = [Role.DON, Role.MAFIA, Role.SHERIFF, Role.DOCTOR] + [Role.CIVILIAN] * 4
        elif n == 9:
            roles_pool = [Role.DON, Role.MAFIA, Role.MAFIA, Role.SHERIFF, Role.DOCTOR] + [Role.CIVILIAN] * 4

        random.shuffle(roles_pool)
        user_ids = list(self.players.keys())
        for uid, role in zip(user_ids, roles_pool):
            self.players[uid].role = role
            if role == Role.DON:
                self.don_user_id = uid
        logger.info("Roles assigned: %s", {p.username: p.role for p in self.players.values()})

    async def start_game(self):
        """Запуск игры: раздача ролей и начало первого дня."""
        if len(self.players) < MIN_PLAYERS:
            raise ValueError("Недостаточно игроков")
        self.assign_roles()
        self._day_number = 0
        await self._start_day()

    # ------------------------------------------------------------------
    # Дневной цикл
    # ------------------------------------------------------------------
    def _init_speaker_order(self):
        # Случайный порядок живых игроков
        alive = [uid for uid, p in self.players.items() if p.is_alive]
        random.shuffle(alive)
        self._speaker_order = alive

    def _rotate_speaker_order(self):
        if not self._speaker_order:
            return
        # Сдвиг: первый становится последним
        self._speaker_order = self._speaker_order[1:] + [self._speaker_order[0]]
        # Убираем мёртвых
        self._speaker_order = [uid for uid in self._speaker_order if self.players[uid].is_alive]

    async def _start_day(self):
        self._day_number += 1
        self.is_first_day = (self._day_number == 1)
        # Сброс номинаций
        for p in self.players.values():
            p.nominated = False
        self.nominated_players.clear()
        self.votes.clear()
        self._vote_change_counts.clear()

        if self._day_number == 1:
            self._init_speaker_order()
        else:
            self._rotate_speaker_order()

        if not self._speaker_order:
            await self._check_win_condition()
            return

        self._current_speaker_index = 0
        await self._change_phase(GamePhase.DAY)
        text = await self.narrator.day_start(self._day_number)
        await self._broadcast_system(text)
        await self._start_player_speech()

    async def _start_player_speech(self):
        if self._current_speaker_index >= len(self._speaker_order):
            await self._after_all_speeches()
            return

        uid = self._speaker_order[self._current_speaker_index]
        self._current_speaker_id = uid
        self._player_nominated_during_speech = False
        self._speaker_nominated_target = None
        player = self.players[uid]

        text = await self.narrator.player_speech(player.username, DAY_SPEECH)
        await self._broadcast_system(text)
        self._speech_timer_task = asyncio.create_task(self._speech_timeout())

    async def _speech_timeout(self):
        await asyncio.sleep(DAY_SPEECH)
        if self._current_speaker_id is None:
            return
        if self._player_nominated_during_speech:
            # Уже номинировал – завершаем без доп. времени
            await self._finish_current_speaker()
        else:
            # Не номинировал – даём дополнительное время на номинацию
            await self._change_phase(GamePhase.NOMINATION)
            text = await self.narrator.nomination_extra(self.players[self._current_speaker_id].username)
            await self._broadcast_system(text)
            self._nomination_timer_task = asyncio.create_task(self._nomination_extra_timeout())

    async def _nomination_extra_timeout(self):
        await self._finish_current_speaker()

    async def _finish_current_speaker(self):
        # Отменяем таймеры речи/номинации
        for task in [self._speech_timer_task, self._nomination_timer_task]:
            if task and not task.done():
                task.cancel()
        self._speech_timer_task = None
        self._nomination_timer_task = None

        speaker_uid = self._current_speaker_id
        if speaker_uid:
            player = self.players.get(speaker_uid)
            if player:
                if self._speaker_nominated_target:
                    target = self.players.get(self._speaker_nominated_target)
                    if target:
                        await self._broadcast_system(f"{player.username} выставляет {target.username}.")
                else:
                    await self._broadcast_system(f"{player.username} воздержался.")

        self._current_speaker_id = None
        self._speaker_nominated_target = None
        self._player_nominated_during_speech = False
        await self._change_phase(GamePhase.DAY)
        self._current_speaker_index += 1
        await self._start_player_speech()

    async def _process_end_turn(self, user_id: str):
        """Обработка досрочного завершения хода."""
        # Для голосования: воздержание
        if self.phase in (GamePhase.VOTING, GamePhase.VOTING_TIE):
            if user_id in self.votes:
                del self.votes[user_id]
            await self._send_personal({"type": "system", "text": "Вы воздержались от голосования."}, user_id)
            return

        # Для защитной речи
        if self.phase in (GamePhase.DEFENSE, GamePhase.DEFENSE_TIE) and user_id == self._current_speaker_id:
            # Отменяем таймер защиты, переходим к следующему
            if self._phase_timer_task and not self._phase_timer_task.done():
                self._phase_timer_task.cancel()
            await self._defense_timeout()
            return

        # Для прощальной минуты
        if self.phase == GamePhase.LAST_WORDS and user_id == self._current_speaker_id:
            if self._last_words_timer_task and not self._last_words_timer_task.done():
                self._last_words_timer_task.cancel()
            await self._end_last_words()
            return

        # Для обычной речи / номинации
        if user_id == self._current_speaker_id:
            await self._finish_current_speaker()

    async def _process_nominate(self, user_id: str, target_username: str):
        if self.is_first_day:
            await self._send_personal({"type": "system", "text": "В первый день нельзя выставлять игроков."}, user_id)
            return
        if user_id != self._current_speaker_id:
            return
        # Один игрок — одна номинация
        if self._speaker_nominated_target is not None:
            return
        if self.phase not in (GamePhase.DAY, GamePhase.NOMINATION):
            return
        target = self._find_player_by_username(target_username)
        if not target or not target.is_alive:
            return
        # Запрет номинировать одного и того же повторно (уже в списке)
        if target.user_id in self.nominated_players:
            return

        target.nominated = True
        self.nominated_players.append(target.user_id)
        self._speaker_nominated_target = target.user_id
        if self.phase == GamePhase.DAY:
            self._player_nominated_during_speech = True

    async def _after_all_speeches(self):
        """Действия после того, как все высказались."""
        # Первый день – сразу ночь
        if self.is_first_day:
            await self._broadcast_system("Первый день – знакомство. Никто не выставляется. Переход к ночи.")
            await self._start_night()
            return
        if not self.nominated_players:
            await self._broadcast_system("Никто не был выставлен. Переход к ночи.")
            await self._start_night()
            return
        if len(self.nominated_players) == 1:
            # Единственный кандидат – сразу прощальная минута, затем исключение
            uid = self.nominated_players[0]
            await self._start_last_words(uid)
            return
        # Несколько кандидатов – защита
        self._defense_queue = self.nominated_players.copy()
        self._current_defense_index = 0
        await self._change_phase(GamePhase.DEFENSE)
        await self._start_defense_speech()

    # ------------------------------------------------------------------
    # Прощальная минута
    # ------------------------------------------------------------------
    async def _start_last_words(self, user_id: str):
        await self._change_phase(GamePhase.LAST_WORDS)
        self._current_speaker_id = user_id
        player = self.players[user_id]
        await self._broadcast_system(f"{player.username} покидает игру. Прощальная минута ({LAST_WORDS_DURATION} сек).")
        await self._start_timer(LAST_WORDS_DURATION, self._end_last_words, '_last_words_timer_task')

    async def _end_last_words(self):
        uid = self._current_speaker_id
        self._current_speaker_id = None
        self._last_words_timer_task = None
        if uid:
            await self._eliminate(uid)
            if not await self._check_win_condition():
                await self._start_night()

    # ------------------------------------------------------------------
    # Защита и голосование
    # ------------------------------------------------------------------
    async def _start_defense_speech(self):
        duration = DEFENSE_DURATION if self.phase == GamePhase.DEFENSE else DEFENSE_TIE_DURATION
        if self._current_defense_index >= len(self._defense_queue):
            if self.phase == GamePhase.DEFENSE:
                await self._start_voting()
            elif self.phase == GamePhase.DEFENSE_TIE:
                await self._start_tie_voting()
            return

        uid = self._defense_queue[self._current_defense_index]
        player = self.players[uid]
        self._current_speaker_id = uid
        text = await self.narrator.defense_speech(player.username, duration)
        await self._broadcast_system(text)
        await self._start_timer(duration, self._defense_timeout)

    async def _defense_timeout(self):
        self._current_speaker_id = None
        self._current_defense_index += 1
        await self._start_defense_speech()

    async def _start_voting(self):
        self.voting_targets = self.nominated_players.copy()
        self.votes.clear()
        self._vote_change_counts.clear()
        await self._change_phase(GamePhase.VOTING)
        text = await self.narrator.voting_start(VOTING_DURATION)
        await self._broadcast_system(text)
        await self._start_timer(VOTING_DURATION, self._on_voting_end)

    async def _on_voting_end(self):
        winners = self._tally_votes()
        # Вывод результатов голосования
        await self._announce_vote_results()
        if len(winners) == 1:
            await self._start_last_words(winners[0])
        elif len(winners) > 1:
            # Повторное голосование (без дополнительной защиты)
            self._defense_queue = winners
            self._current_defense_index = 0
            await self._change_phase(GamePhase.DEFENSE_TIE)
            await self._broadcast_system("Ничья. Переход к повторному голосованию.")
            await self._start_tie_voting()
        else:
            # Никто не голосовал
            await self._broadcast_system("Никто не проголосовал. Переход к ночи.")
            await self._start_night()

    async def _announce_vote_results(self):
        if not self.votes:
            await self._broadcast_system("Никто не отдал голос.")
            return
        lines = []
        counts = {target: 0 for target in self.voting_targets}
        for target in self.votes.values():
            if target in counts:
                counts[target] += 1
        for uid, name in [(uid, self.players[uid].username) for uid in self.voting_targets]:
            lines.append(f"{name}: {counts[uid]} голосов")
        await self._broadcast_system("Результаты голосования:\n" + "\n".join(lines))

    def _tally_votes(self) -> list[str]:
        """Возвращает список user_id кандидатов с максимальным числом голосов."""
        if not self.votes:
            return []
        counts = {target: 0 for target in self.voting_targets}
        for target in self.votes.values():
            if target in counts:
                counts[target] += 1
        max_count = max(counts.values())
        return [uid for uid, c in counts.items() if c == max_count]

    async def _start_tie_voting(self):
        self.voting_targets = self._defense_queue.copy()
        self.votes.clear()
        self._vote_change_counts.clear()
        await self._change_phase(GamePhase.VOTING_TIE)
        text = await self.narrator.voting_start(VOTING_TIE_DURATION)
        await self._broadcast_system(text)
        await self._start_timer(VOTING_TIE_DURATION, self._on_voting_tie_end)

    async def _on_voting_tie_end(self):
        winners = self._tally_votes()
        await self._announce_vote_results()
        if len(winners) == 1:
            await self._start_last_words(winners[0])
        else:
            await self._broadcast_system("Снова ничья. Никто не покидает город.")
            if not await self._check_win_condition():
                await self._start_night()

    async def _eliminate(self, user_id: str):
        player = self.players.get(user_id)
        if player:
            player.is_alive = False
            text = await self.narrator.player_eliminated(player.username)
            await self._broadcast_system(text)
            # Отправляем историю мёртвому
            await self._send_dead_history(user_id)

    # ------------------------------------------------------------------
    # Ночные фазы
    # ------------------------------------------------------------------
    async def _start_night(self):
        await self._change_phase(GamePhase.NIGHT_MAFIA)
        self.mafia_target = None
        self.don_check_target = None
        self.sheriff_check_target = None
        self.doctor_heal_target = None
        self._mafia_votes.clear()
        self._mafia_chat_enabled = True

        text = await self.narrator.mafia_chat_opened()
        await self._broadcast_system(text)
        await self._start_timer(NIGHT_MAFIA_CHAT, self._on_mafia_chat_end)

    async def _on_mafia_chat_end(self):
        self._mafia_chat_enabled = False
        mafia_msg = await self.narrator.mafia_chat_closed()
        await self.send_to_role({"type": "system", "text": mafia_msg}, Role.MAFIA)
        await self.send_to_role({"type": "system", "text": mafia_msg}, Role.DON)
        await self._start_timer(NIGHT_MAFIA_EXTRA, self._on_night_mafia_end)

    async def _on_night_mafia_end(self):
        self.mafia_target = self._resolve_mafia_vote()
        # Если цель не выбрана — убийства не будет

        # Дон
        await self._change_phase(GamePhase.NIGHT_DON)
        don = self.players.get(self.don_user_id)
        if don and don.is_alive and not self._don_found_sheriff:
            text = await self.narrator.don_check()
            await self._broadcast_system(text)
            await self._start_timer(NIGHT_DON_DURATION, self._on_night_don_end)
        else:
            await self._imitate_pause()
            await self._on_night_don_end()

    def _resolve_mafia_vote(self) -> Optional[str]:
        if not self._mafia_votes:
            return None
        # Подсчёт голосов
        freq: dict[str, int] = {}
        for target_id in self._mafia_votes.values():
            freq[target_id] = freq.get(target_id, 0) + 1
        max_votes = max(freq.values())
        top_candidates = [uid for uid, cnt in freq.items() if cnt == max_votes]
        if len(top_candidates) == 1:
            return top_candidates[0]
        # Равенство — приоритет дона
        don = self.players.get(self.don_user_id)
        if don and don.is_alive:
            don_vote = self._mafia_votes.get(self.don_user_id)
            if don_vote in top_candidates:
                return don_vote
        # Иначе случайный
        return random.choice(top_candidates)

    async def _on_night_don_end(self):
        await self._change_phase(GamePhase.NIGHT_SHERIFF)
        sheriff = next((p for p in self.players.values() if p.role == Role.SHERIFF and p.is_alive), None)
        if sheriff:
            text = await self.narrator.sheriff_check()
            await self._broadcast_system(text)
            await self._start_timer(NIGHT_SHERIFF_DURATION, self._on_night_sheriff_end)
        else:
            await self._imitate_pause()
            await self._on_night_sheriff_end()

    async def _on_night_sheriff_end(self):
        await self._change_phase(GamePhase.NIGHT_DOCTOR)
        doctor = next((p for p in self.players.values() if p.role == Role.DOCTOR and p.is_alive), None)
        if doctor:
            text = await self.narrator.doctor_heal()
            await self._broadcast_system(text)
            await self._start_timer(NIGHT_DOCTOR_DURATION, self._on_night_doctor_end)
        else:
            await self._imitate_pause()
            await self._on_night_doctor_end()

    async def _on_night_doctor_end(self):
        await self._resolve_night()
        if not await self._check_win_condition():
            await self._start_day()

    async def _resolve_night(self):
        killed = None
        if self.mafia_target and self.doctor_heal_target != self.mafia_target:
            killed = self.mafia_target
        if killed:
            self.players[killed].is_alive = False
            text = await self.narrator.kill_announcement(self.players[killed].username)
            await self._broadcast_system(text)
            await self._send_dead_history(killed)
        else:
            text = await self.narrator.peaceful_night()
            await self._broadcast_system(text)

        # Результаты проверок
        if self.sheriff_check_target:
            target = self.players.get(self.sheriff_check_target)
            if target:
                role_text = target.role.value
                sheriffs = [p for p in self.players.values() if p.role == Role.SHERIFF and p.is_alive]
                for s in sheriffs:
                    await self._send_personal(
                        {"type": "system", "text": f"Проверка {target.username}: {role_text}."},
                        s.user_id
                    )
        if self.don_check_target:
            target = self.players.get(self.don_check_target)
            if target:
                don = self.players.get(self.don_user_id)
                if don and don.is_alive:
                    is_sheriff = target.role == Role.SHERIFF
                    await self._send_personal(
                        {"type": "system", "text": f"Проверка {target.username}: {'шериф' if is_sheriff else 'не шериф'}."},
                        don.user_id
                    )

    # ------------------------------------------------------------------
    # Проверка победы
    # ------------------------------------------------------------------
    async def _check_win_condition(self) -> bool:
        alive_mafia = sum(1 for p in self.players.values() if p.role in (Role.MAFIA, Role.DON) and p.is_alive)
        alive_others = sum(1 for p in self.players.values() if p.role not in (Role.MAFIA, Role.DON) and p.is_alive)
        if alive_mafia == 0:
            await self._change_phase(GamePhase.GAME_OVER)
            await self.cancel_timers()
            await self._broadcast_system("Мирные жители победили! Мафия уничтожена.")
            return True
        if alive_mafia >= alive_others:
            await self._change_phase(GamePhase.GAME_OVER)
            await self.cancel_timers()
            await self._broadcast_system("Мафия захватила город. Победа мафии!")
            return True
        return False

    # ------------------------------------------------------------------
    # Обработка входящих сообщений
    # ------------------------------------------------------------------
    async def handle_message(self, user_id: str, raw: dict):
        msg_type = raw.get("type")
        if msg_type == "chat":
            await self._process_chat(user_id, raw.get("text", ""))
        elif msg_type == "nominate":
            await self._process_nominate(user_id, raw.get("target", ""))
        elif msg_type == "vote":
            await self._process_vote(user_id, raw.get("target", ""))
        elif msg_type == "action":
            await self._process_night_action(user_id, raw)
        elif msg_type == "end_turn":
            await self._process_end_turn(user_id)

    async def _process_chat(self, user_id: str, text: str):
        player = self.players.get(user_id)
        if not player:
            return
        # Мёртвые общаются только в чате мёртвых
        if not player.is_alive:
            await self._broadcast_dead({"type": "chat", "from": player.username, "text": text})
            return

        # Дневной общий чат
        if self.phase in (GamePhase.DAY, GamePhase.NOMINATION):
            if user_id == self._current_speaker_id and self.phase == GamePhase.DAY:
                await self._broadcast({"type": "chat", "from": player.username, "text": text})
            else:
                await self._send_personal({"type": "system", "text": "Сейчас не ваша очередь говорить."}, user_id)
        elif self.phase in (GamePhase.DEFENSE, GamePhase.DEFENSE_TIE, GamePhase.LAST_WORDS):
            if user_id == self._current_speaker_id:
                await self._broadcast({"type": "chat", "from": player.username, "text": text})
        elif self.phase == GamePhase.NIGHT_MAFIA and player.role in (Role.MAFIA, Role.DON) and self._mafia_chat_enabled:
            msg = {"type": "chat", "from": player.username, "text": text, "mafia_chat": True}
            await self.send_to_role(msg, Role.MAFIA)
            await self.send_to_role(msg, Role.DON)
            self.mafia_chat_log.append(msg)

    async def _process_vote(self, user_id: str, target_username: str):
        if self.phase not in (GamePhase.VOTING, GamePhase.VOTING_TIE):
            return
        voter = self.players.get(user_id)
        target = self._find_player_by_username(target_username)
        if not voter or not target or not voter.is_alive:
            return
        if target.user_id not in self.voting_targets:
            return
        # Лимит смен голоса
        changes = self._vote_change_counts.get(user_id, 0)
        if changes >= 5:
            await self._send_personal({"type": "system", "text": "Вы исчерпали лимит смен голоса (5)."}, user_id)
            return
        self.votes[user_id] = target.user_id
        self._vote_change_counts[user_id] = changes + 1
        await self._send_personal({"type": "system", "text": f"Ваш голос за {target.username} принят."}, user_id)

    async def _process_night_action(self, user_id: str, data: dict):
        action_type = data.get("action")
        target_username = data.get("target")
        actor = self.players.get(user_id)
        target = self._find_player_by_username(target_username) if target_username else None
        if not actor or not actor.is_alive:
            return

        if action_type == "kill" and self.phase in (GamePhase.NIGHT_MAFIA, GamePhase.NIGHT_DON):
            if actor.role in (Role.MAFIA, Role.DON) and target and target.is_alive:
                self._mafia_votes[user_id] = target.user_id
                await self._send_personal({"type": "system", "text": f"Ваш голос за убийство {target.username} учтён."}, user_id)
            else:
                await self._send_personal({"type": "system", "text": "Невозможно выбрать эту цель."}, user_id)

        elif action_type == "check" and self.phase == GamePhase.NIGHT_DON:
            if user_id != self.don_user_id:
                return
            if target and target.user_id != user_id and target.role not in (Role.MAFIA, Role.DON) \
                    and target.user_id not in self._don_checked:
                self.don_check_target = target.user_id
                self._don_checked.add(target.user_id)
                is_sheriff = target.role == Role.SHERIFF
                if is_sheriff:
                    self._don_found_sheriff = True
                await self._send_personal(
                    {"type": "system", "text": f"Вы проверили {target.username}: {'шериф' if is_sheriff else 'не шериф'}."},
                    user_id
                )
            else:
                await self._send_personal({"type": "system", "text": "Нельзя проверить этого игрока."}, user_id)

        elif action_type == "check" and self.phase == GamePhase.NIGHT_SHERIFF:
            if actor.role == Role.SHERIFF and target and target.user_id != user_id \
                    and target.user_id not in self._sheriff_checked:
                self.sheriff_check_target = target.user_id
                self._sheriff_checked.add(target.user_id)
                await self._send_personal(
                    {"type": "system", "text": f"Вы проверили {target.username}: роль {target.role.value}."},
                    user_id
                )
            else:
                await self._send_personal({"type": "system", "text": "Нельзя проверить себя или уже проверенного."}, user_id)

        elif action_type == "heal" and self.phase == GamePhase.NIGHT_DOCTOR:
            if actor.role == Role.DOCTOR and target and target.is_alive:
                if target.user_id == self._last_heal_target:
                    await self._send_personal({"type": "system", "text": "Нельзя лечить одного и того же игрока дважды подряд."}, user_id)
                    return
                self.doctor_heal_target = target.user_id
                self._last_heal_target = target.user_id
                await self._send_personal({"type": "system", "text": f"Вы лечите {target.username}."}, user_id)
            else:
                await self._send_personal({"type": "system", "text": "Невозможно вылечить этого игрока."}, user_id)

    # ------------------------------------------------------------------
    # Коммуникационные утилиты (с учётом test_mode и мёртвых)
    # ------------------------------------------------------------------
    async def _broadcast(self, message: dict, exclude: Optional[list[str]] = None):
        if self.test_mode:
            return
        exclude = exclude or []
        # Живым
        for player in self.players.values():
            if player.user_id in exclude or not player.is_alive:
                continue
            if player.websocket:
                try:
                    await player.websocket.send_json(message)
                except Exception:
                    pass
        # Мёртвым дублируем (если не системное сообщение от ночных проверок)
        if message.get("type") != "action_result":
            self.dead_chat_log.append(message)
            await self._broadcast_dead(message, exclude)

    async def _send_personal(self, message: dict, user_id: str):
        if self.test_mode:
            return
        player = self.players.get(user_id)
        if player and player.websocket:
            try:
                await player.websocket.send_json(message)
            except Exception:
                pass

    async def _broadcast_system(self, text: str):
        msg = {"type": "system", "text": text}
        await self._broadcast(msg)

    async def _broadcast_dead(self, message: dict, exclude: list[str] | None = None):
        """Отправка сообщения всем мёртвым игрокам."""
        exclude = exclude or []
        for player in self.players.values():
            if not player.is_alive and player.user_id not in exclude and player.websocket:
                try:
                    await player.websocket.send_json(message)
                except Exception:
                    pass

    async def _send_dead_history(self, user_id: str):
        """Отправка новому мёртвому всей истории."""
        player = self.players.get(user_id)
        if not player or not player.websocket:
            return
        # Общий лог
        for msg in self.dead_chat_log:
            await self._send_personal(msg, user_id)
        # Лог мафии (если был мафией)
        if player.role in (Role.MAFIA, Role.DON):
            for msg in self.mafia_chat_log:
                await self._send_personal(msg, user_id)
        # Системное сообщение о переходе
        await self._send_personal({"type": "system", "text": "Вы перешли в чат мёртвых. Здесь доступна вся история игры."}, user_id)

    # Публичные обёртки для обратной совместимости
    async def broadcast(self, message: dict, exclude: list[str] | None = None):
        await self._broadcast(message, exclude)

    async def send_personal(self, message: dict, user_id: str):
        await self._send_personal(message, user_id)

    async def send_to_role(self, message: dict, role: Role):
        for player in self.players.values():
            if player.role == role and player.is_alive and player.websocket:
                await self._send_personal(message, player.user_id)

    def handle_disconnect(self, user_id: str):
        player = self.players.get(user_id)
        if player:
            player.websocket = None
            logger.info("Player %s disconnected", player.username)