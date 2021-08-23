# instant_telegrach
Легко развёртываемый движок для имиджборды в Telegram
## Функционал
- Неограниченное количество досок, тредов и постов
- Анонимный постинг
- Бампы 
- Ответы на посты
- Поддержка любых видов медиа
## Требования
Для запуска движка вам понадобятся:
- [python 3](https://www.python.org/downloads/)
- [telethon](https://github.com/LonamiWebs/Telethon#installing)
- `api_id` и `api_hash` (получить можно на [my.telegram.org](https://my.telegram.org))
- бот и токен бота (создать бота и получить токен можно у [@BotFather](https://t.me/BotFather))
- приватный чат в телеграм, играющий роль БД, в который будет добавлен созданный бот и аккаунт, отвечающий за работу с сообщениями в чате-БД
## Конфигурация
Обязательная конфигурация содержится в файле `config.json`
- **`api_id`**: см. Требования
- **`api_hash`**: см. Требования
- **`bot_token`**: токен бота, см. Требования
- **`boards`**: словарь вида `{*буквенный код доски*: *её полное название*}`, количество досок неограничено
- **`salt`**: соль для хеширования идентификаторов пользователей, можно оставить пустой
- **`saving_interval`**: время (в секундах), через которое происходит бекап на диск состояний пользователей и списка тредов
- **`main_text`**: текст на главной странице
- **`rules_text`**: текст на странице с правилами
- **`about_url`**: ссылка, открывающаяся при нажатии "О борде"
- **`db_chat_id`**: id ранее созданного приватного чата, получить можно, добавив в чат [@getmyid_bot](https://t.me/getmyid_bot) или подобного бота

Помимо этого, имеется возможность использовать кастомные изображения. Для этого в папке images необходимо заменить следующие файлы:
- `main.png`: изображение на главной странице
- `rules.png`: изображение в разделе с правилами
- `posting.png`: изображение при отправке поста
- `refuse.png`: изображение при ошибке в создаваемом треде
- `x_banner.png`: изображение на доске с буквенным кодом `x`, при добавлении новых досок в конфиг необходимо добавлять соответствующее изображение
## Запуск
Необходимо запустить файл `main.py`. При вервом запуске нужно ввести номер телефона аккаунта, отвечающего за работу с сообщениями в чате-БД, и затем ввести код подтверждения авторизации Telegram.
## TODO
- Добавить поддержку альбомов
- Более надёжная капча

