from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/face_recognition'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Конфигурация загрузки файлов
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}

# Импорт модулей базы данных и обработки лиц
from database import db, Face
from face_recognition import encode_face, compare_faces, get_image_from_frame, send_telegram_alert

# Инициализация базы данных
db.init_app(app)

# Функция проверки допустимых расширений файлов
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Главная страница веб-интерфейса
@app.route('/')
def index():
    faces = Face.query.all()
    return render_template('index.html', faces=faces)

# Обработка запроса на добавление нового лица
@app.route('/add_face', methods=['POST'])
def add_face():
    """обрабатывает POST-запросы на добавление нового лица в базу данных. Мы получаем имя и файл из запроса, 
проверяем файл на допустимые расширения и сохраняем файл в папке static/uploads. Затем мы обрабатываем файл 
с помощью функции encode_face() из модуля face_recognition, сохраняем закодированное представление лица 
в базу данных и перенаправляем пользователя на главную страницу."""
    # Получение данных из запроса
    name = request.form['name']
    file = request.files['file']
    # Проверка входных данных
    if name and file and allowed_file(file.filename):
        # Загрузка файла
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Обработка файла
        encoding = encode_face(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Сохранение нового лица в базе данных
        face = Face(name=name, encoding=encoding, filename=filename)
        db.session.add(face)
        db.session.commit()
    return redirect(url_for('index'))

# Обработка запроса на распознавание лица с IP-камеры
@app.route('/process_frame', methods=['POST'])
def process_frame():
    """"обрабатывает POST-запросы с кадрами с IP-камеры для распознавания лиц в реальном времени. 
    Мы получаем кадр из запроса и обрабатываем его с помощью функции get_image_from_frame() и encode_face() из модуля face_recognition. 
    Затем мы ищем совпадения в базе данных с помощью функции compare_faces(), и если есть совпадение, 
    то записываем имя лица и название файла в таблицу detection в базе данных. Если же совпадений нет, 
    то мы отправляем изображение в Telegram с помощью функции send_telegram_alert() из модуля face_recognition."""
    
    # Получение данных из запроса
    frame = request.data
    # Обработка кадра
    image = get_image_from_frame(frame)
    encoding = encode_face(image)
    # Поиск совпадений в базе данных
    faces = Face.query.all()
    for face in faces:
        if compare_faces(encoding, face.encoding):
            # Запись в базу данных
            detection = Detection(name=face.name, filename=face.filename)
            db.session.add(detection)
            db.session.commit()
            break
    else:
        # Отправка сообщения в телеграм
        send_telegram_alert(image)
    return 'OK'

# Запуск приложения
""""Мы запускаем приложение с помощью метода run() объекта app. 
Если мы запускаем файл напрямую (а не импортируем его как модуль), то мы устанавливаем переменную __name__ в '__main__'. 
Поэтому мы проверяем, равна ли __name__ '__main__', чтобы запустить приложение только если файл был запущен напрямую."""

if __name__ == '__main__':
    app.run(debug=True)