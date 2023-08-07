# AvitoParser
Бесконечный парсер(скрапер) для авито - запускает Selenium(для сбора номеров телефона в авито) вместе с Tor (для смены ip), отслеживает новые обьявления в категории, и отправляет уведомления в телеграм или на сервер (зависит от настройки в коде). Приостанавливает сбор телефонов ночью, в конце дня отправляет статистику собраных обьявлений.
# Get started
В главном репозитории должен быть репозиторий с torbrowser и репозиторий с gechodriver.

Для отправки сообщений в телеграм, в файле ./src/sender.py добавить в поле класса токен телеграм и id для обьявлений и статистики(admin).

Работает с версией Selenium 4.9.0 (не выше).

Точка входа .src/multiprocessing_main.py

Присутствует логирование для сбора обьявления, сбора телефона и отправки, а также проблемных страниц (если у авито меняется разметка, для адаптирования парсера).

Предупреждение: все модули сильно связаны.
