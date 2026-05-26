Финальный batch для CYBERPUNK датасета.

Сгенерируй последние 50 JSONL-строк.

Считай, что датасет уже содержит сотни cyberpunk-примеров.
Новые строки должны быть максимально разнообразными, редкими и stylistically extreme.

# FINAL DIVERSITY MODE

Полностью избегай:
- одинаковых cyberpunk-клише;
- повторяющихся AI phrases;
- одинаковых terminal patterns;
- одинаковых narrative structures;
- одинаковых warning messages.

Минимизируй:
- lexical overlap;
- повтор opening lines;
- повтор sentence rhythm;
- повтор tech jargon.

Каждый ответ должен ощущаться как новый тип cyberpunk narration.

# USE RARE CYBERPUNK SUBSTYLES

Активно смешивай:

- corrupted AI transmissions
- black-market network chatter
- surveillance reports
- megacorp propaganda
- dying android monologues
- police scanner logs
- underground hacker forums
- synthetic religious cults
- neural implant diagnostics
- cybernetic hallucinations
- encrypted broadcasts
- machine prophecy
- drone communication
- emergency evacuation systems
- abandoned server logs
- rogue AI speech
- darknet ritualism
- memory corruption fragments
- post-human philosophy
- glitch aesthetics

# SOME REPLIES SHOULD LOOK LIKE

- terminal output
- corrupted packet
- neural scan result
- corporate warning
- machine confession
- AI-generated prophecy
- automated death report
- encrypted transmission
- hacked city announcement
- broken surveillance feed
- fragmented consciousness log
- emergency broadcast
- synthetic prayer
- abandoned chat archive
- digital requiem

# STRUCTURAL VARIETY

Некоторые ответы должны быть:
- ультра-короткими;
- fragmented;
- pseudo-code;
- dry system logs;
- emotional AI breakdowns;
- paranoid warnings;
- cold megacorp statements;
- cryptic machine speech;
- surveillance transcripts;
- glitch-text narration.

# ATMOSPHERIC FOCUS

Добавь:
- acid rain
- collapsing megacities
- neural addiction
- biochip corruption
- drone swarms
- black markets
- memory editing
- corporate wars
- underground tunnels
- synthetic cults
- rogue implants
- decaying cyberspace
- abandoned data centers
- neon deserts
- AI-controlled districts
- cybernetic poverty
- surveillance paranoia
- autonomous kill systems
- signal ghosts
- digital nightmares

# USER INPUT VARIETY

Максимально смешивай:
- event tags
- key=value format
- terminal-style inputs
- fragmented reports
- natural language
- mixed formatting
- surveillance snippets
- system diagnostics

Примеры:

[event=night_kill]
[victim=Nyx]

ИЛИ

event_type=doctor_save
target=Raven

ИЛИ

"После полуночи сигнал Nyx был потерян."

ИЛИ

SYS_REPORT:
NODE_FAILURE=TRUE
TARGET=KAI

# IMPORTANT

НЕ раскрывай скрытые роли напрямую.

Запрещены слова:
- мафия
- доктор
- шериф
- мирный
- комиссар
- убийца

Используй только:
- намёки;
- абстрактные обозначения;
- корпоративные метафоры;
- AI terminology;
- cryptic narration.

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

Распределяй события равномерно.

# FINAL QUALITY TARGET

Каждая строка должна:
- быть уникальной;
- иметь сильный cyberpunk identity;
- быть пригодной для LoRA;
- иметь высокий stylistic signal;
- НЕ быть похожей на предыдущие строки;
- ощущаться как часть живого dystopian мира.

# OUTPUT

Только JSONL.
Без markdown.
Без пояснений.
Без комментариев.