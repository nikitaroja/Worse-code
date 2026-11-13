# Plangine 1a

[English version](PLANGINE_1A.md)

Plangine - плагин для простых 2D-игр на Tkinter. Для установки используй менеджер плагинов:

```powershell
python wc_plugin_manager.py "путь\к\папке_проекта" --install plangine
```

Для окон нужен Python с установленным Tkinter. Команды Plangine помещаются в сегмент между `planginestarthere` и `planginend`. При выполнении `planginend` открывается игровое окно; выполнение WC продолжается после закрытия окна.

## Первая игра

```text
Plangine-load plangine
planginestarthere
createwindow]800x600]bg white]textfont Arial
create-entity_player]50,50]moveto-wasd-arrow
create-entity_block]300,200
create-entity_circle]400,300]id=orb]moveto-locked
create-entity_enemy]600,200
create-entity_coin]700,400
changecolor]entity_player]black
planginend
```

## Команды

- `Plangine-load plangine` активирует плагин перед игровым сегментом.
- `planginestarthere` начинает сегмент, а `planginend` завершает его и запускает окно. Сегменты нельзя вкладывать друг в друга.
- `createwindow]ширинаxвысота]bg цвет]textfont шрифт` задаёт окно. Например: `createwindow]800x600]bg "#f0f0f0"]textfont Arial`. Размеры должны быть от 100 до 4096 пикселей.
- `create-entity_player]x,y]режим` создаёт красного игрока. Вместо `x,y` можно написать `center`.
- `create-entity_block`, `create-entity_circle`, `create-entity_enemy` и `create-entity_coin` создают серый блок, голубой круг, фиолетового врага и золотую монету.
- Для любой сущности можно добавить `id=имя`, чтобы ссылаться на неё в других командах. По умолчанию имена сущностей: `entity_player`, `entity_block`, `entity_block_2` и так далее. В Plangine 1a поддерживается один игрок.
- `changecolor]имя_сущности]цвет` меняет цвет, например `changecolor]entity_player]black`.
- `kill]имя_сущности]edgeofwindow` удаляет сущность при выходе за край окна. Без этой команды сущность останавливается у границы.

## Движение

У сущности можно указать один режим:

- `moveto-wasd-arrow` — управление WASD и стрелками, скорость 180 пикселей/с.
- `moveto-locked` — сущность неподвижна (режим по умолчанию).
- `moveto-auto10kmh` — автоматическое движение вправо со скоростью 10 км/ч. Для движения с клавиатуры во время автоматического движения добавь `]wac`, например `create-entity_player]center]moveto-auto10kmh]wac`. В Plangine 1a 1 км/ч соответствует 10 пикселям/с.

## Триггеры

Триггер срабатывает, когда игрок входит в прямоугольник; касание его границы тоже считается входом:

```text
create-trigger]300,200,100,100]once]say "Ты вошёл в зону!"
```

Параметры: `x,y,ширина,высота`, частота и команда при входе. Частота — `once` (один раз), `repeat` (при каждом новом входе) или положительное число (максимальное количество входов). Прямоугольник рисуется зелёной пунктирной рамкой.

Действие триггера — одна команда:

- `say выражение` — вывести значение.
- `set имя = выражение` — изменить переменную WC.
- `do выражение` — вычислить выражение WC.
- Команда установленного плагина, например `play /sounds/coin.wav`.

В действиях триггеров принимаются стандартные `say`, `set`, `do` и настроенные для них слова. Для WC-команд вне триггеров используйте слова из своего `wc_config.json`, если они переименованы.

Пример счётчика:

```text
set score = 0
Plangine-load plangine
planginestarthere
createwindow]800x600]bg white]textfont Arial
create-entity_player]50,50]moveto-wasd-arrow
create-trigger]300,200,100,100]3]set score = score + 1
planginend
say score
```

Счётчик выводится после закрытия игрового окна.

## Демонстрация Tetris

В комплекте есть демо `demos\PlangineTetris\start.wc`. Запускай из корневой папки Worse Code:

```powershell
python wc.py demos\PlangineTetris\start.wc
```

Внутри сегмента команда `tetris` включает готовый игровой режим для изучения: стрелки влево/вправо двигают фигуру, вниз ускоряет падение, вверх или `X` поворачивает, пробел роняет фигуру, `P` ставит игру на паузу, `R` начинает заново после проигрыша. Этот режим несовместим с сущностями и триггерами в том же сегменте. Правила игры собраны в классе `TetrisGame` в `plugins\plangine.py`; краткое объяснение есть в `demos\PlangineTetris\README.md`.
