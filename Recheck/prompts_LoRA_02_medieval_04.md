Финальный batch для DARK_MEDIEVAL датасета.

Сгенерируй последние 50 JSONL-строк.

Считай, что датасет уже содержит сотни примеров.
Новые строки должны быть максимально редкими, необычными и stylistically extreme.

# FINAL DIVERSITY MODE

Полностью избегай:
- стандартных medieval-клише;
- повторяющихся конструкций;
- одинаковых narrative patterns;
- одинаковых emotional cadences.

Минимизируй:
- повтор существительных;
- повтор глаголов;
- повтор opening syntax;
- повтор sentence rhythm.

Каждый ответ должен ощущаться написанным другим рассказчиком.

# USE RARE MEDIEVAL STYLES

Активно смешивай:

- монастырскую латынь
- фанатичные проповеди
- тексты инквизиции
- полубезумные пророчества
- записи умирающего летописца
- обращения палача
- речи крестоносцев
- деревенские суеверия
- plague hysteria
- ritual chants
- funeral sermons
- battlefield reports
- heresy accusations
- apocalyptic scripture
- fragmented cathedral prayers

# SOME REPLIES SHOULD LOOK LIKE

- обрывки хроник
- запись сожжённого монастыря
- приговор инквизиции
- массовая молитва
- рыцарская клятва
- исповедь перед смертью
- приказ военного коменданта
- проклятие
- церковное песнопение
- фрагмент запрещённого манускрипта

# STRUCTURAL VARIETY

Некоторые ответы:
- 1 короткая строка
- 2–3 длинных предложения
- fragmented phrases
- archaic declarations
- ritual repetition
- panic speech
- emotionally broken narration
- ultra-dry chronicles

# ATMOSPHERIC FOCUS

Добавь:
- famine
- frost
- corpse carts
- rotting cathedrals
- fanatic mobs
- ruined monasteries
- burning villages
- muddy battlefields
- dying kings
- false saints
- cursed bells
- ash storms
- black rivers
- plague pits

# USER INPUT VARIETY

Максимально смешивай:
- event tags
- key=value format
- natural language
- partial logs
- fragmented inputs

# IMPORTANT

НЕ раскрывай роли.

НЕ используй:
- мафия
- доктор
- шериф
- мирный
- комиссар
- убийца

Используй только атмосферные намёки.

# EVENTS

Используй только:

DAY_START
VOTING
PLAYER_LYNCHED
NIGHT_START
NIGHT_KILL
SHERIFF_CHECK
DOCTOR_SAVE
GAME_OVER

# FINAL QUALITY TARGET

Каждая строка должна:
- быть уникальной;
- иметь сильный stylistic identity;
- быть пригодной для LoRA;
- не быть похожей на предыдущие;
- создавать ощущение настоящего мира.

# OUTPUT

Только JSONL.
Без markdown.
Без пояснений.
Без комментариев.