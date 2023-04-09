"""
Обратите внимание, что вы должны заменить значения `YOUR_TOKEN` и `YOUR_CHAT_ID` на свои значения для телеграмм бота.
Кроме того, перед использованием этого кода вы должны убедиться, что у вас установлены все необходимые библиотеки, 
а также созданы таблицы в базе данных PostgreSQL, которые используются в запросах (например, таблицы `faces`, `faces_log`).
"""
import cv2
import psycopg2
import telegram
import face_recognition

# Подключение к базе данных PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="mydatabase",
    user="myusername",
    password="mypassword"
)
cur = conn.cursor()

# Инициализация телеграмм бота
bot = telegram.Bot(token='YOUR_TOKEN')

# Загрузка изображений из базы данных PostgreSQL
cur.execute("SELECT name, encoding FROM faces")
known_face_encodings = []
known_face_names = []
for name, encoding in cur.fetchall():
    known_face_encodings.append(encoding)
    known_face_names.append(name)

# Инициализация камеры
cap = cv2.VideoCapture(0)

while True:
    # Захват видео с камеры
    ret, frame = cap.read()

    # Поиск лиц на кадре
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    # Сопоставление найденных лиц с известными лицами
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"
        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]

            # Запись в базу данных PostgreSQL
            cur.execute("INSERT INTO faces_log (name, time) VALUES (%s, now())", (name,))
            conn.commit()

        # Отправка тревоги на телеграмм бота
        else:
            bot.send_photo(chat_id='YOUR_CHAT_ID', photo=open('face.jpg', 'rb'))
        
    # Отображение видео с обведенными лицами
    for (top, right, bottom, left), name in zip(face_locations, names):
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 1)

# Отображение видео в окне
cv2.imshow('Video', frame)

# Обработка нажатия клавиши 'q' для выхода из программы
if cv2.waitKey(1) & 0xFF == ord('q'):
    break

cap.release()
cv2.destroyAllWindows()
conn.close()