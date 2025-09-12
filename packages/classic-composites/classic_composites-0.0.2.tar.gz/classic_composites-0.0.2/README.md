# Classic Composites

Предоставляет утилиту для описания композитов в ленивом стиле.

## Установка

```bash
pip install classic-composites
```

## Rationale

Представим себе, что у нас есть приложение со следующей структурой:

![](./docs/1_modules_structure.drawio.png)

Здесь есть две точки входа, `api_entrypoint` и `worker_entrypoint`.
Каждый из них является композитом, в котором инстанцируются классы с картинок,
затем присходит запуск этих гипотетических классов. 

Если опустить инфраструктурные особенности, вроде кода, считывающего настройки, 
или кода подключения к базам данных, то код `api_entrypoint` 
мог бы выглядеть примерно так:

```python
from types import SimpleNamespace

from example import db, app, api


DB = SimpleNamespace()
DB.interface = db.DBInterface()
DB.some_repo = db.SomeRepo()

APP = SimpleNamespace()
APP.some_query = app.SomeQuery(DB.interface)
APP.some_command = app.SomeCommand(DB.some_repo)

API = SimpleNamespace()
API.some_handler = api.SomeHandler(
    APP.some_query, APP.some_command,
)
API.wsgi_app = api.App(API.some_handler)


if __name__ == '__main__':
    import waitress
    
    waitress.serve(API.wsgi)
```

Код `worker_entrypoint` мог бы выглядеть вот так:
```python
from types import SimpleNamespace

from example import db, app, worker


DB = SimpleNamespace()
DB.some_repo = db.SomeRepo()

APP = SimpleNamespace()
APP.some_command = app.SomeCommand(DB.some_repo)
APP.other_command = app.OtherCommand(DB.some_repo)

WORKER = SimpleNamespace()
WORKER.listener = worker.Listener(
    APP.some_command, APP.other_command,
)


if __name__ == '__main__':
    WORKER.listener.run()
```

Такой пример кода хотя очень прост, все же имеет проблему - дублирование кода.
В этом примере это явно не является проблемой, так как классов мало,
но в реальных системах классов гораздо больше, и там это является проблемой.
Классы db.SomeRepo и app.SomeCommand инстанцируются дважды.
Можно попробовать решить проблему, сделав общий модуль, в котором будут
инстанцированы все объекты, а в entrypoint-ах оставить только импорт нужного 
класса и запуск.

`composite.py`:
```python
from types import SimpleNamespace

from example import db, app, api, worker


DB = SimpleNamespace()
DB.interface = db.DBInterface()
DB.some_repo = db.SomeRepo()

APP = SimpleNamespace()
APP.some_query = app.SomeQuery(DB.interface)
APP.some_command = app.SomeCommand(DB.some_repo)
APP.other_command = app.OtherCommand(DB.some_repo)

API = SimpleNamespace()
API.some_handler = api.SomeHandler(
    APP.some_query, APP.some_command,
)
API.wsgi_app = api.App(API.some_handler)

WORKER = SimpleNamespace()
WORKER.listener = worker.Listener(
    APP.some_command, APP.other_command,
)
```

`api_entrypoint.py`:
```python
import waitress

from .composite import API

waitress.serve(API.wsgi_app)
```

`worker_entrypoint.py`
```python
from .composites import WORKER

WORKER.listener.run()
```

При таком подходе получается минимальное дублирование кода, но создаются 
инстансы для всех объектов, не всегде нужных. Во многих библиотеках встречается
загрузка чего-либо из сетевого источника, или установка соединения с сервером
по умолчанию, что в сочетании с таким подходом приведет к использованию 
лишних ресурсов.

Для решения этой проблемы можно попробовать сделать наш композит ленивым
с помощью лямбда выражений, чтобы объекты создавались не сразу, а отложенно, 
при вызове, чтобы создавать их, когда понадобится.

Для этого завернем каждое инстанцирование объекта в композите в `lambda`,
а при указании какого-либо имени в пространстве имен просто поставим скобки:

`composite.py`
```python
from types import SimpleNamespace

from example import db, app, api, worker


DB = SimpleNamespace()
DB.interface = lambda: db.DBInterface()
DB.some_repo = lambda: db.SomeRepo()

APP = SimpleNamespace()
APP.some_query = lambda: app.SomeQuery(DB.interface())
APP.some_command = lambda: app.SomeCommand(DB.some_repo())
APP.other_command = lambda: app.OtherCommand(DB.some_repo())

API = SimpleNamespace()
API.some_handler = lambda: api.SomeHandler(
    APP.some_query(), APP.some_command(),
)
API.wsgi_app = lambda: api.App(API.some_handler())

WORKER = SimpleNamespace()
WORKER.listener = lambda: worker.Listener(
    APP.some_command(), APP.other_command(),
)
```

После исполнения этого файла в памяти останутся пространства имен, содержащие 
фабрики, но еще не содержащие сами объекты. Тогда, в entry_point остается 
только вызвать нужную функцию:

`api_entrypoint.py`:
```python
import waitress

from .composite import API

waitress.serve(API.wsgi_app())
```

`worker_entrypoint.py`
```python
from .composites import WORKER

WORKER.listener().run()
```

При вызове API.wsgi_app() произойдет вызов фабрики, оттуда, по цепочке,
произойдет вызов API.some_handler(), оттуда APP.some_query() и
APP.some_command(), и т.д., в итоге будут инстанцированы все необходимые
объекты, но те фабрики, на которые не было ссылки, вызваны не будут. 

Здесь все еще есть проблема - фабрики каждый раз возвращают новый объект. Нам 
необходимо свести инстанцирование к минимуму в большинстве случаев, потому бы
хотели сделать себе что-то вроде объекта-кеша, который бы содержал в себе 
результаты вызова фабрик. Что-то вроде:


`composite.py`
```python
from types import SimpleNamespace

from hypotetical_cache import Cache

from example import db, app, api, worker

cache = Cache()

DB = SimpleNamespace()
DB.interface = cache(lambda: db.DBInterface())
DB.some_repo = cache(lambda: db.SomeRepo())

APP = SimpleNamespace()
APP.some_query = cache(lambda: app.SomeQuery(DB.interface()))
APP.some_command = cache(lambda: app.SomeCommand(DB.some_repo()))
APP.other_command = cache(lambda: app.OtherCommand(DB.some_repo()))

API = SimpleNamespace()
API.some_handler = cache(lambda: api.SomeHandler(
    APP.some_query(), APP.some_command(),
))
API.wsgi_app = cache(lambda: api.App(API.some_handler()))

WORKER = SimpleNamespace()
WORKER.listener = cache(lambda: worker.Listener(
    APP.some_command(), APP.other_command(),
))
```

Такой класс нетрудно было бы написать, но использование становится громоздким.
Хотелось бы иметь некоторый синтаксический сахар для этого. И вот для этого
и существует эта библиотека.

Класс Namespace умеет кешировать результаты фабрик по умолчанию:

`composite.py`
```python
from classic.composites import Namespace

from example import db, app, api, worker

DB = Namespace()
DB.interface = db.DBInterface
DB.some_repo = lambda: db.SomeRepo()

APP = Namespace()
APP.some_query = lambda: app.SomeQuery(DB.interface())
APP.some_command = lambda: app.SomeCommand(DB.some_repo())
APP.other_command = lambda: app.OtherCommand(DB.some_repo())

API = Namespace()
API.some_handler = lambda: api.SomeHandler(
    APP.some_query(), APP.some_command(),
)
API.wsgi_app = lambda: api.App(API.some_handler())

WORKER = Namespace()
WORKER.listener = lambda: worker.Listener(
    APP.some_command(), APP.other_command(),
)
```

Выглядит очень похоже на вариант без кеша, только с кешем :)

Также есть способ отключить кеш для нужной фабрики:
```python
from classic.composites import Namespace, no_cache


DB = Namespace()
DB.some_obj = no_cache(lambda: 1)
```
