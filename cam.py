import cv2
import face_recognition
import mysql.connector

# Подключение к базе данных
mydb = mysql.connector.connect(
  host="localhost",
  user="username",
  password="password",
  database="database_name"
)

# Получение ссылки на IP-камеру Xiaomi (XMC01)
video_capture = cv2.VideoCapture('rtsp://user:password@ip_address:554/onvif1')

# Загрузка изображения лица для сравнения
known_image = face_recognition.load_image_file("known_face.jpg")
known_face_encoding = face_recognition.face_encodings(known_image)[0]

while True:
    # Считывание кадра из видеопотока
    ret, frame = video_capture.read()

    # Конвертирование кадра в RGB формат
    rgb_frame = frame[:, :, ::-1]

    # Определение всех лиц на кадре
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for face_encoding in face_encodings:
        # Сравнение лица на кадре с известным лицом
        matches = face_recognition.compare_faces([known_face_encoding], face_encoding)
        if True in matches:
            # Запись в базу данных
            mycursor = mydb.cursor()
            sql = "INSERT INTO faces (name) VALUES (%s)"
            val = ("known_face",)
            mycursor.execute(sql, val)
            mydb.commit()

    # Отображение кадра с выделенными лицами
    for (top, right, bottom, left) in face_locations:
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
    cv2.imshow('Video', frame)

    # Выход при нажатии на клавишу 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождение ресурсов
video_capture.release()
cv2.destroyAllWindows()