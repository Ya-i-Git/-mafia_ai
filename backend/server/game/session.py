import asyncio
import logging
import random
from typing import Optional, Dict, Any, List

from backend.server.game.player import Player
from backend.server.game.roles import Role
from backend.server.game.constants import *
from backend.narrator.phases import GamePhase

from backend.narrator.event import (
    DAY_START,
    NIGHT_START,
    GAME_STORY,
    PLAYER_ELIMINATED,
    KILL_ANNOUNCEMENT,
    PEACEFUL_NIGHT,
)

logger = logging.getLogger(__name__)

try:
    from backend.narrator.generator import generate as ai_generate
    AI_AVAILABLE = True
except ImportError:
    logger.error("Narrator module not found! AI narration will be disabled.")
    AI_AVAILABLE = False


class AINarrator:
    def __init__(self, world: str):
        self.world = world

    async def _call(self, event_type: str, event_data: Dict[str, Any],
                    session_context: Dict[str, Any]) -> str:
        if not AI_AVAILABLE:
            logger.warning("AI is not available, returning empty narration.")
            return ""
        context = {
            "players_alive": session_context.get("players_alive", []),
            "history": session_context.get("history", ""),
            "daily_fact": session_context.get("daily_fact", ""),
        }
        event = {"type": event_type, "data": event_data}
        try:
            return await ai_generate(event, self.world, context)
        except Exception as e:
            logger.error(f"AI generation failed for event {event_type}: {e}")
            return ""


class GameSession:
    def __init__(self, game_id: str, owner_id: str, world: str = "cyberpunk", test_mode: bool = False,
                 narrator: Optional[Any] = None):
        self.game_id = game_id
        self.owner_id = owner_id
        self.world = world
        self.test_mode = test_mode
        self.narrator = narrator or AINarrator(self.world)
        self.history_log: List[str] = []
        self.daily_fact: Optional[str] = None
        self.players: dict[str, Player] = {}
        self.phase = GamePhase.WAITING
        self._phase_timer_task: Optional[asyncio.Task] = None
        self._phase_timer_deadline: Optional[float] = None
        self._pre_game_timer_task: Optional[asyncio.Task] = None
        self._pre_game_timer_deadline: Optional[float] = None
        self._speech_timer_task: Optional[asyncio.Task] = None
        self._speech_timer_deadline: Optional[float] = None
        self._nomination_timer_task: Optional[asyncio.Task] = None
        self._nomination_timer_deadline: Optional[float] = None
        self._last_words_timer_task: Optional[asyncio.Task] = None
        self._last_words_timer_deadline: Optional[float] = None
        self._speaker_order: list[str] = []
        self._current_speaker_index = 0
        self._current_speaker_id: Optional[str] = None
        self._player_nominated_during_speech = False
        self._speaker_nominated_target: Optional[str] = None
        self._day_number = 0
        self.is_first_day = True
        self.nominated_players: list[str] = []
        self.votes: dict[str, str] = {}
        self.voting_targets: list[str] = []
        self._defense_queue: list[str] = []
        self._current_defense_index = 0
        self.mafia_target: Optional[str] = None
        self.don_check_target: Optional[str] = None
        self.sheriff_check_target: Optional[str] = None
        self.doctor_heal_target: Optional[str] = None
        self._mafia_votes: dict[str, str] = {}
        self.don_user_id: Optional[str] = None
        self._don_found_sheriff = False
        self._don_checked: set[str] = set()
        self._sheriff_checked: set[str] = set()
        self._last_heal_target: Optional[str] = None
        self._mafia_chat_enabled = False
        self.dead_chat_log: list[dict] = []
        self.mafia_chat_log: list[dict] = []
        self._timer_updater_task: Optional[asyncio.Task] = None
        self.shuffled_player_ids: list[str] = []
        self._don_acted = False
        self._sheriff_acted = False
        self._doctor_acted = False

        # Для запрета переголосования (пункт 5)
        self._has_voted: dict[str, bool] = {}   # user_id -> already voted in current voting round

    def _find_player_by_username(self, username: str) -> Optional[Player]:
        for p in self.players.values():
            if p.username == username:
                return p
        return None

    def _build_session_context(self) -> Dict[str, Any]:
        return {
            "players_alive": [p.username for p in self.players.values() if p.is_alive],
            "history": "\n".join(self.history_log[-5:]),
            "daily_fact": self.daily_fact,
        }

    async def _narrate(self, event_type: str, event_data: Optional[Dict[str, Any]] = None) -> str:
        if not AI_AVAILABLE:
            return ""
        event_data = event_data or {}
        ctx = self._build_session_context()
        return await self.narrator._call(event_type, event_data, ctx)

    async def _add_history(self, message: str):
        self.history_log.append(message)
        if len(self.history_log) > 10:
            self.history_log = self.history_log[-5:]

    async def _change_phase(self, new_phase: GamePhase):
        self.phase = new_phase
        logger.info("Game %s phase -> %s", self.game_id, new_phase)
        await self.broadcast_game_state()

    async def _start_timer(self, seconds: float, callback, task_attr: str = '_phase_timer_task', deadline_attr: str = '_phase_timer_deadline'):
        task = getattr(self, task_attr, None)
        if task and not task.done():
            task.cancel()

        async def _wait_and_call():
            await asyncio.sleep(seconds)
            await callback()

        new_task = asyncio.create_task(_wait_and_call())
        setattr(self, task_attr, new_task)
        setattr(self, deadline_attr, asyncio.get_event_loop().time() + seconds)

        if self._timer_updater_task is None or self._timer_updater_task.done():
            self._timer_updater_task = asyncio.create_task(self._periodic_state_updater())

    async def _periodic_state_updater(self):
        while True:
            await asyncio.sleep(1)
            if not (self._phase_timer_task or self._pre_game_timer_task or 
                    self._speech_timer_task or self._nomination_timer_task or 
                    self._last_words_timer_task):
                break
            await self.broadcast_game_state()

    async def cancel_timers(self):
        for task in [self._phase_timer_task, self._speech_timer_task,
                     self._nomination_timer_task, self._last_words_timer_task,
                     self._pre_game_timer_task, self._timer_updater_task]:
            if task and not task.done():
                task.cancel()
        self._phase_timer_task = None
        self._speech_timer_task = None
        self._nomination_timer_task = None
        self._last_words_timer_task = None
        self._pre_game_timer_task = None
        self._timer_updater_task = None
        self._phase_timer_deadline = None
        self._pre_game_timer_deadline = None
        self._speech_timer_deadline = None
        self._nomination_timer_deadline = None
        self._last_words_timer_deadline = None

    async def _pause_between_phases(self, seconds: int = 3):
        await asyncio.sleep(seconds)

    def _get_remaining_time(self) -> int:
        now = asyncio.get_event_loop().time()
        if self.phase == GamePhase.PRE_GAME and self._pre_game_timer_deadline:
            remaining = self._pre_game_timer_deadline - now
            return max(0, int(remaining))

        deadline = None
        if self.phase == GamePhase.DAY and self._speech_timer_deadline:
            deadline = self._speech_timer_deadline
        elif self.phase == GamePhase.NOMINATION and self._nomination_timer_deadline:
            deadline = self._nomination_timer_deadline
        elif self.phase == GamePhase.LAST_WORDS and self._last_words_timer_deadline:
            deadline = self._last_words_timer_deadline
        elif self._phase_timer_deadline:
            deadline = self._phase_timer_deadline

        if deadline:
            remaining = deadline - now
            return max(0, int(remaining))
        return 0

    def add_player(self, user_id: str, username: str) -> Player:
        if user_id in self.players:
            raise ValueError("Игрок уже в игре")
        if any(p.username == username for p in self.players.values()):
            raise ValueError("Игрок с таким именем уже в игре")
        if self.phase != GamePhase.WAITING:
            raise ValueError("Игра уже началась, нельзя присоединиться")
        player = Player(user_id, username)
        self.players[user_id] = player
        asyncio.create_task(self.broadcast_game_state())
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
        self._don_checked.clear()
        self._sheriff_checked.clear()
        self._don_found_sheriff = False
        logger.info("Roles assigned: %s", {p.username: p.role for p in self.players.values()})

    def _shuffle_players(self):
        all_ids = list(self.players.keys())
        random.shuffle(all_ids)
        self.shuffled_player_ids = all_ids
        for idx, uid in enumerate(self.shuffled_player_ids):
            self.players[uid].number = idx + 1

    def _update_speaker_order(self):
        live = [uid for uid in self.shuffled_player_ids if self.players[uid].is_alive]
        if not live:
            self._speaker_order = []
            self._current_speaker_index = 0
            return
        offset = (self._day_number - 1) % len(live)
        self._speaker_order = live[offset:] + live[:offset]
        self._current_speaker_index = 0
        logger.info(f"Day {self._day_number} speaker order: {[self.players[uid].username for uid in self._speaker_order]}")

    async def _clear_nominations(self):
        for p in self.players.values():
            p.nominated = False
        self.nominated_players.clear()

    async def _start_pre_game(self):
        await self._change_phase(GamePhase.PRE_GAME)
        self.assign_roles()

        mafia_ids = [uid for uid, p in self.players.items() if p.role in (Role.MAFIA, Role.DON)]
        mafia_usernames = [self.players[uid].username for uid in mafia_ids]
        don_username = self.players[self.don_user_id].username if self.don_user_id else None
        for uid in mafia_ids:
            await self._send_personal({
                "type": "mafia_team",
                "members": mafia_usernames,
                "don": don_username
            }, uid)

        for player in self.players.values():
            if player.websocket:
                await self._send_personal(
                    {"type": "role_assigned", "role": player.role.value},
                    player.user_id
                )
                await self._send_personal(
                    {"type": "player_number", "number": player.number},
                    player.user_id
                )

        self._shuffle_players()
        for player in self.players.values():
            player.is_alive = True

        story = await self._narrate(GAME_STORY, {})
        await self._broadcast_system(story)
        await self._add_history(story)
        await self.broadcast_game_state()
        await self._broadcast_system("🎲 Игра начинается...")
        await self._start_timer(PRE_GAME_DURATION, self._begin_game, '_pre_game_timer_task', '_pre_game_timer_deadline')

    async def _begin_game(self):
        if self._pre_game_timer_task:
            self._pre_game_timer_task = None
        await self._broadcast_system("Город просыпается. Начинается день.")
        await self._pause_between_phases()
        await self._start_day()

    async def start_game(self):
        if self.phase != GamePhase.WAITING:
            raise ValueError("Игра уже началась")
        if len(self.players) < MIN_PLAYERS:
            raise ValueError(f"Недостаточно игроков. Нужно минимум {MIN_PLAYERS}")
        await self._start_pre_game()
        await self.broadcast_game_state()

    async def _start_day(self):
        self._day_number += 1
        self.is_first_day = (self._day_number == 1)
        for p in self.players.values():
            p.nominated = False
        self.nominated_players.clear()
        self.votes.clear()
        self._has_voted.clear()          # очищаем флаги голосования для нового дня
        self._update_speaker_order()
        if not self._speaker_order:
            await self._check_win_condition()
            return
        await self._change_phase(GamePhase.DAY)
        text = await self._narrate(DAY_START, {"day_number": self._day_number})
        await self._broadcast_system(text)
        await self._add_history(text)
        await self.broadcast_game_state()
        await self._pause_between_phases()
        await self._start_player_speech()

    async def _start_player_speech(self):
        if self._current_speaker_index >= len(self._speaker_order):
            await self._after_all_speeches()
            return
        uid = self._speaker_order[self._current_speaker_index]
        self._current_speaker_id = uid
        player = self.players[uid]
        await asyncio.sleep(3)
        await self._broadcast_system(f"🎤 Сейчас говорит {player.username}")
        await self.broadcast_game_state()
        await self._start_timer(DAY_SPEECH, self._speech_timeout, '_speech_timer_task', '_speech_timer_deadline')

    async def _speech_timeout(self):
        if self._current_speaker_id is None:
            return
        if self._player_nominated_during_speech:
            await self._finish_current_speaker()
        else:
            await self._change_phase(GamePhase.NOMINATION)
            await self._broadcast_system("Время на речь закончилось. Есть 15 секунд, чтобы выдвинуть игрока.")
            await self.broadcast_game_state()
            await self._start_timer(DAY_NOMINATION_EXTRA, self._finish_current_speaker, '_nomination_timer_task', '_nomination_timer_deadline')

    async def _finish_current_speaker(self):
        for task_name, deadline_name in [('_speech_timer_task', '_speech_timer_deadline'),
                                         ('_nomination_timer_task', '_nomination_timer_deadline')]:
            task = getattr(self, task_name, None)
            if task and not task.done():
                task.cancel()
            setattr(self, task_name, None)
            setattr(self, deadline_name, None)

        speaker_uid = self._current_speaker_id
        self._current_speaker_id = None
        self._player_nominated_during_speech = False
        if speaker_uid and not self.is_first_day and self._speaker_nominated_target is None:
            player = self.players.get(speaker_uid)
            if player:
                await self._broadcast_system(f"{player.username} воздержался от номинации.")
        self._speaker_nominated_target = None
        await self._change_phase(GamePhase.DAY)
        self._current_speaker_index += 1
        await self.broadcast_game_state()
        await self._start_player_speech()

    async def _process_end_turn(self, user_id: str):
        # Пункт 4: убираем отзыв голоса, а также не даём завершать ход мёртвым
        player = self.players.get(user_id)
        if not player or not player.is_alive:
            return

        if self.phase in (GamePhase.VOTING, GamePhase.VOTING_TIE):
            # Ничего не делаем, голос не отзывается
            await self._send_personal({"type": "system", "text": "Сейчас нельзя завершить ход."}, user_id)
            return

        if self.phase == GamePhase.DAY and user_id == self._current_speaker_id:
            if self._speech_timer_task and not self._speech_timer_task.done():
                self._speech_timer_task.cancel()
            await self._finish_current_speaker()
            return
        if self.phase == GamePhase.NOMINATION and user_id == self._current_speaker_id:
            if self._nomination_timer_task and not self._nomination_timer_task.done():
                self._nomination_timer_task.cancel()
            await self._finish_current_speaker()
            return
        if self.phase in (GamePhase.DEFENSE, GamePhase.DEFENSE_TIE) and user_id == self._current_speaker_id:
            if self._phase_timer_task and not self._phase_timer_task.done():
                self._phase_timer_task.cancel()
            await self._defense_timeout()
            return
        if self.phase == GamePhase.LAST_WORDS and user_id == self._current_speaker_id:
            if self._last_words_timer_task and not self._last_words_timer_task.done():
                self._last_words_timer_task.cancel()
            await self._end_last_words()
            return

    async def _process_nominate(self, user_id: str, target_username: str):
        if self.is_first_day:
            await self._send_personal({"type": "system", "text": "В первый день нельзя выставлять игроков."}, user_id)
            return
        if user_id != self._current_speaker_id:
            return
        if self._speaker_nominated_target is not None:
            return
        if self.phase not in (GamePhase.DAY, GamePhase.NOMINATION):
            return
        target = self._find_player_by_username(target_username)
        if not target or not target.is_alive:
            return
        if target.user_id == user_id:
            await self._send_personal({"type": "system", "text": "Нельзя выдвигать себя."}, user_id)
            return
        if target.user_id in self.nominated_players:
            return
        target.nominated = True
        self.nominated_players.append(target.user_id)
        self._speaker_nominated_target = target.user_id
        if self.phase == GamePhase.DAY:
            self._player_nominated_during_speech = True
        await self._broadcast_system(f"{self.players[user_id].username} выдвигает {target.username}.")
        if self.phase == GamePhase.NOMINATION:
            if self._nomination_timer_task and not self._nomination_timer_task.done():
                self._nomination_timer_task.cancel()
            await self._finish_current_speaker()

    async def _after_all_speeches(self):
        if self.is_first_day:
            msg = "Первый день – знакомство. Никто не выставляется. Переход к ночи."
            await self._broadcast_system(msg)
            await self._add_history(msg)
            await self._start_night()
            return
        if not self.nominated_players:
            msg = "Никто не был выставлен. Переход к ночи."
            await self._broadcast_system(msg)
            await self._add_history(msg)
            await self._start_night()
            return
        if len(self.nominated_players) == 1:
            uid = self.nominated_players[0]
            await self._start_last_words(uid)
            return
        self._defense_queue = self.nominated_players.copy()
        self._current_defense_index = 0
        await self._change_phase(GamePhase.DEFENSE)
        await self._start_defense_speech()

    async def _start_last_words(self, user_id: str):
        await self._change_phase(GamePhase.LAST_WORDS)
        self._current_speaker_id = user_id
        player = self.players[user_id]
        text = await self._narrate(PLAYER_ELIMINATED, {"username": player.username})
        await self._broadcast_system(text)
        await self._add_history(text)
        await self._broadcast_system(f"{player.username} покидает игру. Прощальная минута ({LAST_WORDS_DURATION} сек).")
        await self.broadcast_game_state()
        await self._start_timer(LAST_WORDS_DURATION, self._end_last_words, '_last_words_timer_task', '_last_words_timer_deadline')

    async def _end_last_words(self):
        uid = self._current_speaker_id
        self._current_speaker_id = None
        self._last_words_timer_task = None
        self._last_words_timer_deadline = None
        if uid:
            await self._eliminate(uid)
            await self._clear_nominations()
            if not await self._check_win_condition():
                await self._start_night()
        await self.broadcast_game_state()

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
        await self._broadcast_system(f"🎤 Слово для защиты у {player.username} ({duration} сек).")
        await self.broadcast_game_state()
        await self._start_timer(duration, self._defense_timeout, '_phase_timer_task', '_phase_timer_deadline')

    async def _defense_timeout(self):
        self._current_speaker_id = None
        self._current_defense_index += 1
        await self._start_defense_speech()

    async def _start_voting(self):
        self.voting_targets = self.nominated_players.copy()
        self.votes.clear()
        self._has_voted.clear()      # новый раунд голосования
        await self._change_phase(GamePhase.VOTING)
        await self._broadcast_system(f"Голосование! У вас {VOTING_DURATION} секунд. Выберите игрока.")
        await self.broadcast_game_state()
        await self._start_timer(VOTING_DURATION, self._on_voting_end, '_phase_timer_task', '_phase_timer_deadline')

    async def _on_voting_end(self):
        await self._clear_nominations()
        winners = self._tally_votes()
        await self._announce_vote_results()
        if len(winners) == 1:
            await self._start_last_words(winners[0])
        elif len(winners) > 1:
            self._defense_queue = winners
            self._current_defense_index = 0
            await self._change_phase(GamePhase.DEFENSE_TIE)
            msg = "Ничья. Переход к повторному голосованию."
            await self._broadcast_system(msg)
            await self._add_history(msg)
            await self.broadcast_game_state()
            await self._start_tie_voting()
        else:
            msg = "Никто не проголосовал. Переход к ночи."
            await self._broadcast_system(msg)
            await self._add_history(msg)
            await self.broadcast_game_state()
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
        for uid in self.voting_targets:
            name = self.players[uid].username
            lines.append(f"{name}: {counts[uid]} голосов")
        await self._broadcast_system("Результаты голосования:\n" + "\n".join(lines))

    def _tally_votes(self) -> list[str]:
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
        self._has_voted.clear()      # новый раунд голосования
        await self._change_phase(GamePhase.VOTING_TIE)
        await self._broadcast_system(f"Повторное голосование! {VOTING_TIE_DURATION} секунд.")
        await self.broadcast_game_state()
        await self._start_timer(VOTING_TIE_DURATION, self._on_voting_tie_end, '_phase_timer_task', '_phase_timer_deadline')

    async def _on_voting_tie_end(self):
        await self._clear_nominations()
        winners = self._tally_votes()
        await self._announce_vote_results()
        if len(winners) == 1:
            await self._start_last_words(winners[0])
        else:
            msg = "Снова ничья. Никто не покидает город."
            await self._broadcast_system(msg)
            await self._add_history(msg)
            await self.broadcast_game_state()
            if not await self._check_win_condition():
                await self._start_night()

    async def _eliminate(self, user_id: str):
        player = self.players.get(user_id)
        if player:
            player.is_alive = False
            self._update_speaker_order()
            await self._send_dead_history(user_id)
            await self.broadcast_game_state()

    async def _start_night(self):
        await self._change_phase(GamePhase.NIGHT_MAFIA)
        self.mafia_target = None
        self.don_check_target = None
        self.sheriff_check_target = None
        self.doctor_heal_target = None
        self._mafia_votes.clear()
        self._mafia_chat_enabled = True
        self._don_acted = False
        self._sheriff_acted = False
        self._doctor_acted = False
        night_msg = await self._narrate(NIGHT_START, {})
        await self._broadcast_system(night_msg)
        await self._add_history(night_msg)
        await self._pause_between_phases()
        await self._broadcast_system("Мафия, просыпайтесь! У вас минута на обсуждение.")
        await self.broadcast_game_state()
        await self._start_timer(NIGHT_MAFIA_CHAT, self._on_mafia_chat_end, '_phase_timer_task', '_phase_timer_deadline')

    async def _on_mafia_chat_end(self):
        self._mafia_chat_enabled = False
        await self.send_to_role({"type": "system", "text": "Время обсуждения вышло. Мафия, голосуйте за жертву (у вас 15 секунд)."}, Role.MAFIA)
        await self.send_to_role({"type": "system", "text": "Время обсуждения вышло. Дон, голосуйте за жертву (у вас 15 секунд)."}, Role.DON)
        await self._start_timer(NIGHT_MAFIA_EXTRA, self._on_night_mafia_end, '_phase_timer_task', '_phase_timer_deadline')

    async def _on_night_mafia_end(self):
        self.mafia_target = self._resolve_mafia_vote()
        await self._start_don_phase()

    def _all_mafia_voted(self) -> bool:
        alive_mafia = [uid for uid, p in self.players.items() 
                       if p.is_alive and p.role in (Role.MAFIA, Role.DON)]
        if not alive_mafia:
            return True
        voted = set(self._mafia_votes.keys())
        return all(uid in voted for uid in alive_mafia)

    async def _start_night_phase(self, phase: GamePhase, duration: int, next_callback, action_allowed: bool = True):
        await self._change_phase(phase)
        if action_allowed:
            if phase == GamePhase.NIGHT_DON:
                await self._broadcast_system("Дон, вы можете проверить одного игрока.")
            elif phase == GamePhase.NIGHT_SHERIFF:
                await self._broadcast_system("Шериф, вы можете проверить одного игрока.")
            elif phase == GamePhase.NIGHT_DOCTOR:
                await self._broadcast_system("Доктор, выберите, кого лечить.")
        else:
            await self._broadcast_system("Город замирает в ожидании...")
        await self.broadcast_game_state()
        await self._start_timer(duration, next_callback, '_phase_timer_task', '_phase_timer_deadline')

    async def _start_don_phase(self):
        don = self.players.get(self.don_user_id)
        if don and don.is_alive and not self._don_found_sheriff and not self._don_acted:
            await self._start_night_phase(GamePhase.NIGHT_DON, NIGHT_DON_DURATION, self._start_sheriff_phase, action_allowed=True)
        else:
            pause = random.uniform(5, 30)
            await self._start_night_phase(GamePhase.NIGHT_DON, pause, self._start_sheriff_phase, action_allowed=False)

    async def _start_sheriff_phase(self):
        sheriff = next((p for p in self.players.values() if p.role == Role.SHERIFF and p.is_alive), None)
        if sheriff and not self._sheriff_acted:
            await self._start_night_phase(GamePhase.NIGHT_SHERIFF, NIGHT_SHERIFF_DURATION, self._start_doctor_phase, action_allowed=True)
        else:
            pause = random.uniform(5, 30)
            await self._start_night_phase(GamePhase.NIGHT_SHERIFF, pause, self._start_doctor_phase, action_allowed=False)

    async def _start_doctor_phase(self):
        doctor = next((p for p in self.players.values() if p.role == Role.DOCTOR and p.is_alive), None)
        if doctor and not self._doctor_acted:
            await self._send_personal({
                "type": "doctor_last_heal",
                "target_id": self._last_heal_target
            }, doctor.user_id)
            await self._start_night_phase(GamePhase.NIGHT_DOCTOR, NIGHT_DOCTOR_DURATION, self._end_night, action_allowed=True)
        else:
            pause = random.uniform(5, 30)
            await self._start_night_phase(GamePhase.NIGHT_DOCTOR, pause, self._end_night, action_allowed=False)

    async def _end_night(self):
        await self._resolve_night()
        if not await self._check_win_condition():
            await self._start_day()

    def _resolve_mafia_vote(self) -> Optional[str]:
        if not self._mafia_votes:
            return None
        freq: dict[str, int] = {}
        for target_id in self._mafia_votes.values():
            freq[target_id] = freq.get(target_id, 0) + 1
        max_votes = max(freq.values())
        top_candidates = [uid for uid, cnt in freq.items() if cnt == max_votes]
        if len(top_candidates) == 1:
            return top_candidates[0]
        don = self.players.get(self.don_user_id)
        if don and don.is_alive:
            don_vote = self._mafia_votes.get(self.don_user_id)
            if don_vote in top_candidates:
                return don_vote
        return random.choice(top_candidates)

    async def _resolve_night(self):
        killed = None
        if self.mafia_target and self.doctor_heal_target != self.mafia_target:
            killed = self.mafia_target
        if killed:
            self.players[killed].is_alive = False
            self._update_speaker_order()
            text = await self._narrate(KILL_ANNOUNCEMENT, {"username": self.players[killed].username})
            await self._broadcast_system(text)
            await self._add_history(text)
            await self._send_dead_history(killed)
        else:
            text = await self._narrate(PEACEFUL_NIGHT, {})
            await self._broadcast_system(text)
            await self._add_history(text)

        if self.sheriff_check_target:
            target = self.players.get(self.sheriff_check_target)
            if target:
                role_text = "мафия" if target.role in (Role.MAFIA, Role.DON) else "мирный"
                sheriffs = [p for p in self.players.values() if p.role == Role.SHERIFF and p.is_alive]
                for s in sheriffs:
                    await self._send_personal(
                        {"type": "system", "text": f"Проверка {target.username}: роль {role_text}."},
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

    async def _check_win_condition(self) -> bool:
        alive_mafia = sum(1 for p in self.players.values() if p.role in (Role.MAFIA, Role.DON) and p.is_alive)
        alive_others = sum(1 for p in self.players.values() if p.role not in (Role.MAFIA, Role.DON) and p.is_alive)
        if alive_mafia == 0:
            await self._change_phase(GamePhase.GAME_OVER)
            await self.cancel_timers()
            win_msg = "Мирные жители победили! Мафия уничтожена."
            await self._broadcast_system(win_msg)
            await self._add_history(win_msg)
            await self.broadcast_game_state()
            return True
        if alive_mafia >= alive_others:
            await self._change_phase(GamePhase.GAME_OVER)
            await self.cancel_timers()
            win_msg = "Мафия захватила город. Победа мафии!"
            await self._broadcast_system(win_msg)
            await self._add_history(win_msg)
            await self.broadcast_game_state()
            return True
        return False

    async def handle_message(self, user_id: str, raw: dict):
        msg_type = raw.get("type")
        player = self.players.get(user_id)
        if not player:
            return

        # Пункт 2: мёртвые не могут выполнять игровые действия (кроме чата)
        if not player.is_alive and msg_type != "chat":
            await self._send_personal({"type": "system", "text": "Вы мертвы и не можете это делать."}, user_id)
            return

        if self.phase == GamePhase.PRE_GAME:
            if msg_type == "chat":
                await self._process_chat(user_id, raw.get("text", ""))
            else:
                await self._send_personal(
                    {"type": "system", "text": "Игра ещё не началась. Дождитесь отсчёта."},
                    user_id
                )
            return

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
        if not player.is_alive:
            await self._broadcast_dead({"type": "chat", "from": player.username, "text": text})
            return
        if self.phase in (GamePhase.DAY, GamePhase.NOMINATION):
            if user_id == self._current_speaker_id:
                await self._broadcast({"type": "chat", "from": player.username, "text": text}, exclude=[user_id])
            else:
                await self._send_personal({"type": "system", "text": "Сейчас не ваша очередь говорить."}, user_id)
        elif self.phase in (GamePhase.DEFENSE, GamePhase.DEFENSE_TIE, GamePhase.LAST_WORDS):
            if user_id == self._current_speaker_id:
                await self._broadcast({"type": "chat", "from": player.username, "text": text}, exclude=[user_id])
        elif self.phase == GamePhase.NIGHT_MAFIA and player.role in (Role.MAFIA, Role.DON) and self._mafia_chat_enabled:
            msg = {"type": "chat", "from": player.username, "text": text, "mafia_chat": True}
            await self.send_to_role(msg, Role.MAFIA, exclude=[user_id])
            await self.send_to_role(msg, Role.DON, exclude=[user_id])
            self.mafia_chat_log.append(msg)

    async def _process_vote(self, user_id: str, target_username: str):
        # Пункт 5: запрет переголосования
        if self.phase not in (GamePhase.VOTING, GamePhase.VOTING_TIE):
            return
        voter = self.players.get(user_id)
        target = self._find_player_by_username(target_username)
        if not voter or not target or not voter.is_alive:
            return
        if target.user_id not in self.voting_targets:
            return
        if self._has_voted.get(user_id, False):
            await self._send_personal({"type": "system", "text": "Вы уже проголосовали. Голос менять нельзя."}, user_id)
            return

        self.votes[user_id] = target.user_id
        self._has_voted[user_id] = True
        await self._send_personal({"type": "system", "text": f"Ваш голос за {target.username} принят."}, user_id)
        await self.broadcast_game_state()

    async def _process_night_action(self, user_id: str, data: dict):
        action_type = data.get("action")
        target_username = data.get("target")
        actor = self.players.get(user_id)
        target = self._find_player_by_username(target_username) if target_username else None
        if not actor or not actor.is_alive:
            return

        if action_type == "kill" and self.phase == GamePhase.NIGHT_MAFIA:
            if actor.role in (Role.MAFIA, Role.DON) and target and target.is_alive:
                self._mafia_votes[user_id] = target.user_id
                await self._send_personal({"type": "system", "text": f"Ваш голос за убийство {target.username} учтён."}, user_id)
                if self._all_mafia_voted():
                    if self._phase_timer_task and not self._phase_timer_task.done():
                        self._phase_timer_task.cancel()
                    await self._on_night_mafia_end()
            else:
                await self._send_personal({"type": "system", "text": "Невозможно выбрать эту цель."}, user_id)

        elif action_type == "check" and self.phase == GamePhase.NIGHT_DON:
            if user_id != self.don_user_id or self._don_acted:
                return
            if self._don_found_sheriff:
                await self._send_personal({"type": "system", "text": "Дон уже нашёл шерифа и больше не может проверять."}, user_id)
                return
            if not target or not target.is_alive:
                await self._send_personal({"type": "system", "text": "Цель должна быть жива."}, user_id)
                return
            if target.user_id == user_id or target.role in (Role.MAFIA, Role.DON) or target.user_id in self._don_checked:
                await self._send_personal({"type": "system", "text": "Нельзя проверить этого игрока."}, user_id)
                return
            self.don_check_target = target.user_id
            self._don_checked.add(target.user_id)
            is_sheriff = target.role == Role.SHERIFF
            if is_sheriff:
                self._don_found_sheriff = True
            await self._send_personal(
                {"type": "system", "text": f"Вы проверили {target.username}: {'шериф' if is_sheriff else 'не шериф'}."},
                user_id
            )
            self._don_acted = True
            if self._phase_timer_task and not self._phase_timer_task.done():
                self._phase_timer_task.cancel()
            await self._start_sheriff_phase()

        elif action_type == "check" and self.phase == GamePhase.NIGHT_SHERIFF:
            if actor.role != Role.SHERIFF or self._sheriff_acted:
                return
            if not target or not target.is_alive:
                await self._send_personal({"type": "system", "text": "Цель должна быть жива."}, user_id)
                return
            if target.user_id == user_id or target.user_id in self._sheriff_checked:
                await self._send_personal({"type": "system", "text": "Нельзя проверить себя или уже проверенного."}, user_id)
                return
            self.sheriff_check_target = target.user_id
            self._sheriff_checked.add(target.user_id)
            self._sheriff_acted = True
            role_text = "мафия" if target.role in (Role.MAFIA, Role.DON) else "мирный"
            await self._send_personal(
                {"type": "system", "text": f"Вы проверили {target.username}: роль {role_text}."},
                user_id
            )
            if self._phase_timer_task and not self._phase_timer_task.done():
                self._phase_timer_task.cancel()
            await self._start_doctor_phase()

        elif action_type == "heal" and self.phase == GamePhase.NIGHT_DOCTOR:
            if actor.role != Role.DOCTOR or self._doctor_acted:
                return
            if not target or not target.is_alive:
                await self._send_personal({"type": "system", "text": "Цель должна быть жива."}, user_id)
                return
            if target.user_id == self._last_heal_target:
                await self._send_personal({"type": "system", "text": "Нельзя лечить одного и того же игрока дважды подряд."}, user_id)
                return
            self.doctor_heal_target = target.user_id
            self._last_heal_target = target.user_id
            self._doctor_acted = True
            await self._send_personal({"type": "system", "text": f"Вы лечите {target.username}."}, user_id)
            if self._phase_timer_task and not self._phase_timer_task.done():
                self._phase_timer_task.cancel()
            await self._end_night()

    async def _broadcast(self, message: dict, exclude: Optional[list[str]] = None, include_dead: bool = False):
        if self.test_mode:
            return
        exclude = exclude or []
        for player in self.players.values():
            if player.user_id in exclude:
                continue
            if not player.is_alive and not include_dead:
                continue
            if player.websocket:
                try:
                    await player.websocket.send_json(message)
                except Exception:
                    pass

        # Для живых сообщения также логируем в dead_chat_log, если это не служебное
        if message.get("type") not in ("action_result", "game_state"):
            self.dead_chat_log.append(message)
            if len(self.dead_chat_log) > 200:
                self.dead_chat_log = self.dead_chat_log[-200:]

        # Отправляем мёртвым всегда (если не исключены)
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

    async def _broadcast_dead(self, message: dict, exclude: Optional[list[str]] = None):
        exclude = exclude or []
        for player in self.players.values():
            if not player.is_alive and player.user_id not in exclude and player.websocket:
                try:
                    await player.websocket.send_json(message)
                except Exception:
                    pass

        # Пункт 3: сохраняем все сообщения мёртвых в историю
        # (но не дублируем те, что уже сохранены в _broadcast)
        # Для простоты – сохраняем только если тип не "action_result"
        if message.get("type") not in ("action_result", "game_state"):
            self.dead_chat_log.append(message)
            if len(self.dead_chat_log) > 200:
                self.dead_chat_log = self.dead_chat_log[-200:]

    async def _send_dead_history(self, user_id: str):
        player = self.players.get(user_id)
        if not player or not player.websocket:
            return
        for msg in self.dead_chat_log:
            await self._send_personal(msg, user_id)
        if player.role in (Role.MAFIA, Role.DON):
            for msg in self.mafia_chat_log:
                await self._send_personal(msg, user_id)
        await self._send_personal({"type": "system", "text": "Вы перешли в чат мёртвых. Здесь доступна вся история игры."}, user_id)

    async def broadcast(self, message: dict, exclude: Optional[list[str]] = None):
        await self._broadcast(message, exclude)

    async def send_personal(self, message: dict, user_id: str):
        await self._send_personal(message, user_id)

    async def send_to_role(self, message: dict, role: Role, exclude: Optional[list[str]] = None):
        exclude = exclude or []
        for player in self.players.values():
            if player.role == role and player.is_alive and player.user_id not in exclude and player.websocket:
                await self._send_personal(message, player.user_id)

    def handle_disconnect(self, user_id: str):
        player = self.players.get(user_id)
        if player:
            player.websocket = None
            logger.info("Player %s disconnected", player.username)
            if self.phase == GamePhase.WAITING:
                self.players.pop(user_id, None)
                asyncio.create_task(self.broadcast_game_state())
            else:
                asyncio.create_task(self.broadcast({"type": "system", "text": f"{player.username} отключился. Ожидаем переподключения."}))

    def get_game_state(self) -> dict:
        players_data = [
            {
                "id": uid,
                "username": p.username,
                "is_alive": p.is_alive,
                "nominated": p.nominated,
                "number": p.number,
            }
            for uid, p in self.players.items()
        ]
        return {
            "phase": self.phase.value,
            "day_number": self._day_number,
            "players": players_data,
            "time_left": self._get_remaining_time(),
            "nominated_players": self.nominated_players,
            "voting_targets": self.voting_targets,
            "current_speaker_id": self._current_speaker_id,
            "owner_id": self.owner_id,
        }

    async def broadcast_game_state(self):
        # Пункт 1: отправляем состояние и живым, и мёртвым
        state = self.get_game_state()
        await self._broadcast({"type": "game_state", "state": state}, include_dead=True)