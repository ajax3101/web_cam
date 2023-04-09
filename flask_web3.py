from flask import Flask, render_template, request, redirect, url_for
import os
import face_recognition
import psycopg2
import telegram

app = Flask(__name__)

# Параметры подключения к базе данных
DB_NAME = 'mydb'
DB_USER = 'myuser'
DB_PASSWORD = 'mypassword'
DB_HOST = 'localhost'
DB_PORT = '5432'

# Параметры Telegram бота
TELEGRAM_TOKEN = 'mytoken'
TELEGRAM_CHAT_ID = 'mychatid'

# Папка для загрузки фотографий
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

# Подключение к базе данных
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

# Функция для проверки расширения файла
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Функция для кодирования изображения лица
def encode_face(image_file):
    image = face_recognition.load_image_file(image_file)
    encoding = face_recognition.face_encodings(image)[0]
    return encoding.tobytes()

# Функция для получения изображения из кадра
def get_image_from_frame(frame):
    image = face_recognition.load_image_file(frame)
    return image

# Функция для сравнения лиц
def compare_faces(known_faces, face_to_compare):
    results = face_recognition.compare_faces(known_faces, face_to_compare)
    index = None
    if True in results:
        index = results.index(True)
    return index

# Функция для отправки уведомления в Telegram
def send_telegram_alert(image_file):
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    caption = 'Неизвестное лицо обнаружено!'
    bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=open(image_file, 'rb'), caption=caption)

# Главная страница
@app.route('/')
def index():
    cursor = conn.cursor()
    cursor.execute('SELECT name, filename FROM faces')
    faces = [{'name': name, 'filename': filename} for name, filename in cursor]
    cursor.close()
    return render_template('index.html', faces=faces)

# Добавление нового лица
@app.route('/add_face', methods=['POST'])
def add_face():
    name = request.form['name']
    file = request.files['file']
    if file and allowed_file(file.filename):
        # Сохраняем файл на сервере
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filename)
        # Кодируем изображение лица и сохраняем в базе данных
        encoding = encode_face(filename)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO faces (name, filename, encoding) VALUES (%s, %s, %s)',
                       (name, filename, psycopg2.Binary(encoding)))
        conn.commit()
        cursor.close()
        # Перенаправляем пользователя на главную страницу
        return redirect(url_for('index'))
    else:
        # Если файл не подходящего формата, возвращаем ошибку
        return 'Неподходящий формат файла'

def recognize_faces():
    # Захватываем видеопоток с IP-камеры
    cap = cv2.VideoCapture('rtsp://user:password@ip_address:port/h264_stream')
    while True:
        # Получаем кадр с камеры
        ret, frame = cap.read()
        if ret:
            # Конвертируем кадр в чёрно-белый
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Находим лица на кадре
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
            # Для каждого найденного лица
            for (x, y, w, h) in faces:
                # Вырезаем лицо из кадра
                face = frame[y:y+h, x:x+w]
                # Кодируем лицо
                encoding = encode_face(face)
                cursor = conn.cursor()
                # Ищем совпадения в базе данных
                cursor.execute('SELECT * FROM faces')
                rows = cursor.fetchall()
                found = False
                for row in rows:
                    name, filename, enc = row
                    if compare_faces(encoding, enc):
                        # Если нашли совпадение, записываем имя и время в базу данных
                        cursor.execute('INSERT INTO matches (name, timestamp) VALUES (%s, %s)',
                                       (name, datetime.now()))
                        conn.commit()
                        found = True
                        break
                cursor.close()
                if not found:
                    # Если не нашли совпадения, отправляем фотографию на телеграмм
                    filename = f'{datetime.now().strftime("%Y%m%d%H%M%S%f")}.jpg'
                    cv2.imwrite(os.path.join(UPLOAD_FOLDER, filename), face)
                    send_telegram_photo(filename)
        else:
            # Если кадр не получен, ждём 1 секунду
            time.sleep(1)
    cap.release()

   
