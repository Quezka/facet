"""Русский перевод интерфейса Facet."""

NAMES: dict[str, list[str]] = {}

# English singular -> (one, few, many) forms.
PLURALS = {
    "separate part": ("отдельная часть", "отдельные части", "отдельных частей"),
}

MESSAGES = {
    # ---- window and pages
    "Facet": "Facet",
    "Home": "Главная",
    "Viewer": "Просмотр",
    "More": "Ещё",
    "Start": "Начать",
    "Recent": "Недавние",
    "Settings": "Настройки",
    "Settings…": "Настройки…",
    "Close": "Закрыть",
    "All files": "Все файлы",
    "3D models": "3D-модели",
    "PNG pictures": "Изображения PNG",
    "Look at 3D models, and measure the ones that need it.":
        "Смотрите 3D-модели и измеряйте те, что этого требуют.",
    "Open a model": "Открыть модель",
    "Open a model…": "Открыть модель…",
    "Open…": "Открыть…",
    "Opening…": "Открытие…",
    "Opening {name}…": "Открытие {name}…",
    "STL, OBJ, PLY or 3MF": "STL, OBJ, PLY или 3MF",
    "Sample part": "Пример детали",
    "A plate with a hole, to try measuring": "Пластина с отверстием, чтобы попробовать измерения",
    "Sample shape": "Пример формы",
    "A smooth vase, a curved model": "Гладкая ваза, модель с кривизной",
    "Drag a file onto the window to open it. In the view: drag to turn, right-drag or Shift-drag to move, wheel to zoom.":
        "Перетащите файл в окно, чтобы открыть его. В окне просмотра: перетаскивание — вращение, правая кнопка или Shift — сдвиг, колесо — масштаб.",
    "No model open.": "Модель не открыта.",
    "triangles": "треугольников",
    "Something went wrong: {error}": "Что-то пошло не так: {error}",
    "Quit Facet": "Выйти из Facet",
    "About Facet": "О программе Facet",
    "A light 3D model viewer, for models you look at and models you measure.":
        "Лёгкий просмотрщик 3D-моделей: для тех, что смотрят, и тех, что измеряют.",
    "Free software under the GNU General Public License, version 3 or later.":
        "Свободное ПО под лицензией GNU General Public License версии 3 или новее.",
    "Restart Facet now": "Перезапустить Facet",
    "The 3D view couldn't start on this computer.":
        "3D-вид не удалось запустить на этом компьютере.",

    # ---- toolbar
    "Solid": "Сплошная",
    "Edges": "Рёбра",
    "Wire": "Каркас",
    "Grid": "Сетка",
    "Grid: {step}": "Сетка: {step}",
    "Box size": "Габариты",
    "Flat view": "Плоский вид",
    "Orthographic view: no perspective, parallel lines stay parallel (O)":
        "Ортогональный вид: без перспективы, параллельные линии остаются параллельными (O)",
    "View": "Вид",
    "Front": "Спереди",
    "Back": "Сзади",
    "Left": "Слева",
    "Right": "Справа",
    "Top": "Сверху",
    "Bottom": "Снизу",
    "Isometric": "Изометрия",
    "Fit": "Вписать",
    "Fit the model to the window (F)": "Вписать модель в окно (F)",
    "Picture": "Снимок",
    "Save picture…": "Сохранить снимок…",
    "Save picture": "Сохранить снимок",
    "Copy picture": "Копировать снимок",
    "Previous model in the folder  (Alt+Left)": "Предыдущая модель в папке  (Alt+←)",
    "Next model in the folder  (Alt+Right)": "Следующая модель в папке  (Alt+→)",

    # ---- details
    "Details": "Сведения",
    "Copy these details": "Копировать сведения",
    "The model's units": "Единицы модели",
    "Width (X)": "Ширина (X)",
    "Depth (Y)": "Глубина (Y)",
    "Height (Z)": "Высота (Z)",
    "Volume": "Объём",
    "Surface area": "Площадь поверхности",
    "Weight": "Вес",
    "Centre of mass": "Центр масс",
    "Triangles": "Треугольники",
    "File": "Файл",
    "Material": "Материал",
    "The weight is for a solid part; a printed one with infill weighs less.":
        "Вес указан для цельной детали; напечатанная с заполнением весит меньше.",

    # ---- mesh check
    "Mesh check": "Проверка сетки",
    "Open a model to check it.": "Откройте модель, чтобы проверить её.",
    "Checking the mesh…": "Проверка сетки…",
    "This model is too big to check its mesh.": "Модель слишком большая для проверки сетки.",
    "Watertight: a closed solid, ready to print.": "Герметична: замкнутое тело, готово к печати.",
    "{edges} open edges: the surface has holes or gaps.": "Открытых рёбер: {edges}. В поверхности есть дыры или щели.",
    "{edges} edges shared by more than two faces.": "Рёбер, общих для более чем двух граней: {edges}.",
    "The faces point inwards (inside out).": "Грани направлены внутрь (модель вывернута).",
    "{n} triangles with no area.": "Треугольников без площади: {n}.",
    "{n} vertices": "вершин: {n}",

    # ---- measuring
    "Measure": "Измерения",
    "Off": "Выкл.",
    "Distance": "Расстояние",
    "Angle": "Угол",
    "Hole": "Отверстие",
    "Supplement": "Смежный",
    "Diameter": "Диаметр",
    "Radius": "Радиус",
    "Snap to corners and edges": "Привязка к вершинам и рёбрам",
    "Pick a tool, then click points on the model. Angle: the corner is the second point. Hole: three points around it.":
        "Выберите инструмент и щёлкайте точки на модели. Угол: вершина — вторая точка. Отверстие: три точки по его краю.",
    "Copy": "Копировать",
    "Remove": "Удалить",
    "Clear": "Очистить",
    "Click the first point": "Щёлкните первую точку",
    "Click the second point": "Щёлкните вторую точку",
    "Click a point on the first side": "Щёлкните точку на первой стороне",
    "Click the corner of the angle": "Щёлкните вершину угла",
    "Click a point on the second side": "Щёлкните точку на второй стороне",
    "Click a point on the hole or curve": "Щёлкните точку на отверстии или кривой",
    "Click a second point on it": "Щёлкните вторую точку на нём",
    "Click a third point on it": "Щёлкните третью точку на нём",
    "Pick three different points.": "Выберите три разные точки.",
    "The three points are in a line: pick points around the hole.":
        "Три точки лежат на одной прямой: выберите точки вокруг отверстия.",
    "That point isn't on the model.": "Эта точка не на модели.",

    # ---- section and look
    "Section": "Сечение",
    "Cut the model with a plane": "Разрезать модель плоскостью",
    "Keep the other side": "Оставить другую сторону",
    "Look": "Внешний вид",
    "Smooth shading": "Плавное затенение",
    "Use the colours stored in the file": "Использовать цвета из файла",
    "Clay": "Глина",
    "Indigo": "Индиго",
    "Amber": "Янтарь",
    "Mint": "Мята",
    "Rose": "Роза",
    "Steel": "Сталь",
    "White": "Белый",

    # ---- settings
    "Appearance": "Оформление",
    "System": "Системная",
    "Light": "Светлая",
    "Dark": "Тёмная",
    "High contrast (black and white, thick lines)": "Высокая контрастность (чёрное и белое, толстые линии)",
    "Numbers": "Числа",
    "Decimal places in measurements": "Знаков после запятой в измерениях",
    "The units (mm, cm, m, inches) are chosen next to the model.":
        "Единицы (мм, см, м, дюймы) выбираются рядом с моделью.",
    "Language": "Язык",
    "Interface language": "Язык интерфейса",
    "Interface size": "Размер интерфейса",
    "Automatic": "Автоматически",
    "Applies after a restart. Automatic is a comfortable, slightly larger size.":
        "Применяется после перезапуска. «Автоматически» — удобный, чуть увеличенный размер.",
    "Updates": "Обновления",
    "Check for new versions once a day": "Проверять новые версии раз в день",
    "Check now": "Проверить сейчас",
    "You have version {version}.": "У вас версия {version}.",

    # ---- updates
    "Check for updates…": "Проверить обновления…",
    "Update available": "Доступно обновление",
    "Facet {version} is available": "Доступен Facet {version}",
    "You have {version}. Here's what's new:": "У вас {version}. Что нового:",
    "No release notes.": "Описания версии нет.",
    "Update now": "Обновить сейчас",
    "Later": "Позже",
    "Skip this version": "Пропустить эту версию",
    "Open download page": "Открыть страницу загрузки",
    "Downloading…": "Загрузка…",
    "Downloading… {done} of {total} MB": "Загрузка… {done} из {total} МБ",
    "Installing… your system may ask for your password.":
        "Установка… система может запросить пароль.",
    "No updates": "Обновлений нет",
    "You have the latest version of Facet ({version}).": "У вас последняя версия Facet ({version}).",
    "Couldn't check for updates": "Не удалось проверить обновления",
    "Can't reach GitHub to check for updates. Check your internet connection.":
        "Не удаётся связаться с GitHub. Проверьте подключение к интернету.",
    "GitHub is limiting update checks right now: try again in an hour.":
        "GitHub сейчас ограничивает проверки обновлений: повторите через час.",
    "GitHub sent an answer Facet doesn't understand.": "GitHub прислал ответ, который Facet не понимает.",
    "There's no download for this computer in that release.":
        "В этой версии нет загрузки для этого компьютера.",
    "The download didn't finish. Check your internet connection and try again.":
        "Загрузка не завершилась. Проверьте подключение к интернету и повторите.",
    "The download was damaged (its checksum doesn't match), so it wasn't installed. Try again.":
        "Загрузка повреждена (контрольная сумма не совпала), поэтому она не установлена. Повторите.",
    "This copy of Facet can't update itself (for example when it runs from source). Download the new version from GitHub.":
        "Эта копия Facet не может обновляться сама (например, при запуске из исходников). Скачайте новую версию с GitHub.",
    "This copy of Facet can't update itself.": "Эта копия Facet не может обновляться сама.",
    "Couldn't start the installer.": "Не удалось запустить установщик.",
    "Installing was cancelled.": "Установка отменена.",

    # ---- errors from the use cases
    "No model is open.": "Модель не открыта.",
    "Facet can't open this kind of file.": "Facet не может открыть файл такого типа.",
    "The file couldn't be read.": "Не удалось прочитать файл.",
    "This file is damaged.": "Файл повреждён.",
    "This file has no triangles in it.": "В файле нет треугольников.",
    "This doesn't look like an STL file.": "Это не похоже на файл STL.",
    "This STL file is damaged or empty.": "Файл STL повреждён или пуст.",
    "This OBJ file is damaged.": "Файл OBJ повреждён.",
    "This OBJ file has no faces.": "В файле OBJ нет граней.",
    "This doesn't look like a PLY file.": "Это не похоже на файл PLY.",
    "This PLY file is damaged.": "Файл PLY повреждён.",
    "This PLY file has no faces.": "В файле PLY нет граней.",
    "This doesn't look like a 3MF file.": "Это не похоже на файл 3MF.",
    "This 3MF file is damaged.": "Файл 3MF повреждён.",
    "This 3MF file has no model in it.": "В файле 3MF нет модели.",
    "This 3MF file has no mesh in it.": "В файле 3MF нет сетки.",
}
