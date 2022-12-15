# Архитектура Компьютера. Лабораторная работа №3.

## Вариант
`alg | acc | harv | hw | instr | struct | stream | mem | prob5`

* `alg`: java-подобный язык.
* `acc`: все вычисления построены вокруг регистра **AC**, выполняющего роль аккумулятора.
* `harv`: Гарвардская архитектура.
* `hw`: Control Unit реализован как часть модели, микрокода нет.
* `instr`: каждая инструкция расписана по-тактово, но в журнале фиксируется только результат выполнения
* `struct` заменено на `binary`: в связи с тем, что данные и инструкции должны храниться в общей памяти, каждая инструкция представляет собой 16-и битное число
* `stream`: ввод-вывод реализован как поток данных
* `mem`: mem-mapped isa

## Язык

* Обьявление через ключевое слово `let`.
* Доступны переменный типа `string` и `number`.
* Доступен цикл `while(number)`.
* Функция `print(number|string)`.
* Функция `scan()` считывает значение.
* Разрешенные математические операции: `+`(бинарный плюс), `-`(бинарный минус),`=`(присваивание), `%`(остаток от деления), `*`(умножение).

## BNF
#### `<program> ::= <term>`
#### `<name> ::= [a-zA-Z]+`
#### `<term> ::= <variable initialization> | <while loop> | <print function> | <term> <term>`
#### `<value> ::= <number> | <string>`
#### `<number> ::= javascript number`
#### `<string> ::= javascript string`
#### `<variable initialization> ::= let <name> = <value>`
#### `<operation> ::= + | - | % | * | > | <`
#### `<print> ::= print(<value>)`
#### `<scan> ::= scan(<value>)`

## Набор инструкций

| Syntax | Mnemonic | Кол-во тактов  | Циклы                                | Comment                                                     |
|:-------|:---------|:---------------|:-------------------------------------|:------------------------------------------------------------|
| `1xxx` | ADD M    | 1              | Command<br/> Operand <br/> Execution | AC + DR -> AC; set ZR                                       |
| `2xxx` | SUB M    | 1              | Command<br/> Operand <br/> Execution | AC + DR -> AC; set ZR                                       |
| `3xxx` | LOOP M   | 1              | Command<br/> Operand <br/> Execution | if (DR > 0) IP + 1 -> IP                                    |
| `4xxx` | LD M     | 1              | Command<br/> Operand <br/> Execution | DR -> CR                                                    |
| `5xxx` | ST M     | 3              | Command<br/> Execution               | DR(0-11) -> DR <br/> DR -> AR; AC -> DR <br/> DR -> MEM(AR) |
| `6xxx` | JUMP M   | 1              | Command<br/> Execution               | DR(0-11) -> DR; DR(0-11) -> IP                              |
| `7xxx` | JZ M     | 1              | Command<br/> Execution               | if (ZR == 1) DR(0-11) -> DR; DR(0-11) -> IP                 |
| `F100` | HLT      | 0              | Command<br/> Execution               | stop                                                        |
| `F200` | CLA      | 1              | Command<br/> Execution               | 0 -> AC; 1 -> ZR                                            |
| `F300` | INC      | 1              | Command<br/> Execution               | AC + 1 -> AC; set ZR                                        |
| `F400` | DEC      | 1              | Command<br/> Execution               | AC - 1 -> AC; set ZR                                        | 
| `F500` | OUT      | 1              | Command<br/> Execution               | write to buffer                                             |

### Циклы

| Цикл            | Кол-во тактов | Comment                                                   | 
|:----------------|:--------------|:----------------------------------------------------------|
| Command Fetch   | 3             | IP -> AR <br/> MEM(AR) -> DR; IP + 1 -> IP <br/> DR -> CR | 
| Operand Fetch   | 3             | DR(0-11) -> DR <br/> DR -> AR <br/> MEM(AR) -> DR         | 
| Execution Fetch | -             | См. описание команды                                      |
