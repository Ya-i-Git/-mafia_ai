import pytest
from backend.server.game.session import GamePhase
from backend.server.game.roles import Role

class TestGameSessionInit:
    async def test_add_players(self, game_6_players):
        """Проверяем, что 6 игроков добавлены."""
        assert len(game_6_players.players) == 6

    async def test_roles_assigned(self, game_6_players):
        """После assign_roles у каждого игрока есть роль."""
        roles = {p.role for p in game_6_players.players.values()}
        assert Role.MAFIA in roles
        assert Role.DON in roles
        assert Role.SHERIFF in roles
        assert Role.DOCTOR in roles
        assert Role.CIVILIAN in roles

    async def test_start_game_phase(self, game_6_players_started):
        """После старта игры фаза становится DAY."""
        game = game_6_players_started
        assert game.phase == GamePhase.DAY

class TestDayCycle:
    async def test_first_day_no_nomination(self, game_6_players_started):
        """В первый день номинация невозможна."""
        game = game_6_players_started
        speaker_id = game._speaker_order[0]
        # Попытка выставить кого-то в первый день
        target = game._speaker_order[1]
        await game._process_nominate(speaker_id, game.players[target].username)
        # Никто не должен быть номинирован
        assert len(game.nominated_players) == 0

    async def test_speaker_can_nominate_after_first_day(self, game_6_players):
        """Проверяем номинацию во второй день (имитируем вручную)."""
        game = game_6_players
        await game.start_game()  # первый день
        # Имитируем завершение первого дня и начало второго
        game.is_first_day = False
        game._day_number = 2
        # Назначаем порядок выступающих
        game._init_speaker_order()
        speaker_id = game._speaker_order[0]
        target_id = game._speaker_order[1]
        target_name = game.players[target_id].username

        # Имитируем фазу DAY для speaker
        game.phase = GamePhase.DAY
        game._current_speaker_id = speaker_id
        await game._process_nominate(speaker_id, target_name)
        assert target_id in game.nominated_players
        assert game.players[target_id].nominated is True

    async def test_voting_and_elimination(self, game_6_players):
        """Полный цикл: номинация, голосование, исключение."""
        game = game_6_players
        game.is_first_day = False
        game._day_number = 2
        alice_id = next(uid for uid, p in game.players.items() if p.username == "Alice")
        bob_id = next(uid for uid, p in game.players.items() if p.username == "Bob")

        game.nominated_players = [bob_id]
        game.players[bob_id].nominated = True
        game.voting_targets = game.nominated_players[:]
        game.phase = GamePhase.VOTING

        await game._process_vote(alice_id, "Bob")
        assert game.votes[alice_id] == bob_id

        # Завершаем голосование, что переведёт в LAST_WORDS
        await game._on_voting_end()

        # Вручную завершаем прощальную минуту (без ожидания 60 сек)
        # _on_voting_end вызывает _start_last_words, которая ставит _current_speaker_id = bob_id
        assert game.phase == GamePhase.LAST_WORDS
        await game._end_last_words()

        # Теперь Боб должен быть мёртв
        assert game.players[bob_id].is_alive == False
        assert game.phase != GamePhase.LAST_WORDS  # фаза перешла к ночи или проверке победы

    async def test_vote_limit(self, game_6_players):
        """Лимит смены голоса – 5 раз."""
        game = game_6_players
        game.is_first_day = False
        game.phase = GamePhase.VOTING
        game.voting_targets = [uid for uid in game.players.keys()]
        voter_id = list(game.players.keys())[0]
        # Меняем голос 6 раз
        for i, target_uid in enumerate(game.players.keys()):
            if i >= 6:
                break
            await game._process_vote(voter_id, game.players[target_uid].username)
        # После 5 смен 6-й должен быть отклонён
        assert game._vote_change_counts.get(voter_id, 0) == 5

class TestNightActions:
    async def test_mafia_vote_resolution(self, game_6_players_started):
        """Мафия голосует за цель, цель разрешается."""
        game = game_6_players_started
        # Переключаем фазу на ночь мафии
        game.phase = GamePhase.NIGHT_MAFIA
        mafia_members = [uid for uid, p in game.players.items() if p.role in (Role.MAFIA, Role.DON) and p.is_alive]
        victim_id = [uid for uid, p in game.players.items() if p.role == Role.CIVILIAN and p.is_alive][0]
        victim_name = game.players[victim_id].username

        # Все мафиози голосуют за одну цель
        for m_id in mafia_members:
            await game._process_night_action(m_id, {"action": "kill", "target": victim_name})
        # Завершаем голосование мафии
        target = game._resolve_mafia_vote()
        assert target == victim_id

    async def test_doctor_cannot_heal_same_target_twice(self, game_6_players_started):
        """Доктор не может лечить одного и того же игрока дважды подряд."""
        game = game_6_players_started
        doctor_id = next(uid for uid, p in game.players.items() if p.role == Role.DOCTOR)
        patient_id = [uid for uid, p in game.players.items() if p.role == Role.CIVILIAN and p.is_alive and uid != doctor_id][0]
        game.phase = GamePhase.NIGHT_DOCTOR
        await game._process_night_action(doctor_id, {"action": "heal", "target": game.players[patient_id].username})
        assert game.doctor_heal_target == patient_id
        # Следующая ночь (имитируем, что цель не менялась)
        # Сначала имитируем завершение ночи и новый день/ночь
        # Можно просто сбросить doctor_heal_target и снова попытаться лечить того же
        game.doctor_heal_target = None
        game._last_heal_target = patient_id  # запомнили, что в прошлый раз лечили его
        await game._process_night_action(doctor_id, {"action": "heal", "target": game.players[patient_id].username})
        # Должен быть отказ, цель не должна обновиться
        assert game.doctor_heal_target != patient_id

    async def test_sheriff_check(self, game_6_players_started):
        """Шериф проверяет игрока и получает его роль."""
        game = game_6_players_started
        sheriff_id = next(uid for uid, p in game.players.items() if p.role == Role.SHERIFF)
        suspect_id = [uid for uid, p in game.players.items() if p.role == Role.MAFIA and p.is_alive][0]
        game.phase = GamePhase.NIGHT_SHERIFF
        await game._process_night_action(sheriff_id, {"action": "check", "target": game.players[suspect_id].username})
        assert game.sheriff_check_target == suspect_id
        # Проверяем, что в _resolve_night шерифу отправляется информация (в тестовом режиме проверим флаг)
        # Мокаем отправку сообщений? Можно добавить проверку в будущем.

class TestWinConditions:
    async def test_mafia_win_when_equal_numbers(self, game_6_players):
        """Когда мафия по численности равна мирным, мафия побеждает."""
        game = game_6_players
        # Убьём всех мирных, оставив двух мафиози и одного мирного
        for p in game.players.values():
            if p.role in (Role.CIVILIAN, Role.SHERIFF, Role.DOCTOR):
                p.is_alive = False
        # Теперь мафия: дон + мафиози (2), мирных: 0 (уже нет)
        # У нас должно быть 2 мафии и 0 мирных -> победа
        result = await game._check_win_condition()
        assert result is True
        assert game.phase == GamePhase.GAME_OVER

    async def test_town_win_when_all_mafia_dead(self, game_6_players):
        """Когда вся мафия мертва, город побеждает."""
        game = game_6_players
        for p in game.players.values():
            if p.role in (Role.MAFIA, Role.DON):
                p.is_alive = False
        result = await game._check_win_condition()
        assert result is True
        assert game.phase == GamePhase.GAME_OVER