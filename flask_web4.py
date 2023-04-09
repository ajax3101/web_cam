import os
import cv2
import time
import psycopg2
import telegram
import numpy as np
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename


# Параметры приложения
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
TELEGRAM_BOT_TOKEN = 'your_bot_token'
TELEGRAM_CHAT_ID = 'your_chat_id'
DATABASE_URL = 'postgres://user:password@host:port/database_name'

# Инициализация приложения
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Инициализация базы данных
conn = psycopg2.connect(DATABASE_URL)

# Инициализация каскада Хаара для распознавания лиц
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


def allowed_file(filename):
    # Проверка расширения файла
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def encode_face(face):
    # Кодирование лица с помощью библиотеки face_recognition
    # Возвращает вектор признаков длиной 128
    # Для этого необходимо установить библиотеку dlib
    import face_recognition
    encoding = face_recognition.face_encodings(face)
    if encoding:
        return encoding[0]
    else:
        return None


def compare_faces(encoding1, encoding2):
    # Сравнение двух векторов признаков лица
    # Возвращает True, если расстояние между ними меньше 0.6
    # Иначе возвращает False
    if encoding1 is None or encoding2 is None:
        return False
    distance = np.linalg.norm(encoding1 - encoding2)
    return distance < 0.6


def send_telegram_photo(filename):
    # Отправка фотографии на телеграмм
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=open(os.path.join(UPLOAD_FOLDER, filename), 'rb'))


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
                # Ищем лица на изображении и записываем результаты в базу данных
                faces = face_recognition.face_locations(rgb_frame, model='hog')
                encodings = face_recognition.face_encodings(rgb_frame, faces)
                for encoding, face_location in zip(encodings, faces):
                    top, right, bottom, left = face_location
                    # Сравниваем лицо с известными лицами в базе данных
                    matches = face_recognition.compare_faces(data["encodings"], encoding)
                    name = "Unknown"
                    # Если найдено совпадение, записываем имя в базу данных
                    if True in matches:
                        matched_idxs = [i for (i, b) in enumerate(matches) if b]
                        counts = {}
                        for i in matched_idxs:
                            name = data["names"][i]
                            counts[name] = counts.get(name, 0) + 1
                        name = max(counts, key=counts.get)
                        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cur.execute("INSERT INTO faces (name, timestamp) VALUES (%s, %s)", (name, ts))
                        conn.commit()
                    # Если не найдено совпадений, отправляем уведомление в Telegram
                    else:
                        image_path = os.path.join(image_folder, f"unknown_{ts}.jpg")
                        cv2.imwrite(image_path, frame)
                        send_telegram_alert(image_path)

                # Отображаем результат на экране
                for ((top, right, bottom, left), name) in zip(faces_locations, names):
                    # Рисуем прямоугольник вокруг лица
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    # Рисуем имя лица под прямоугольником
                    cv2.putText(frame, name, (left, bottom + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.imshow("Video", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            # Освобождаем ресурсы
            cv2.destroyAllWindows()
            vs.stop()
            cur.close()
            conn.close()

