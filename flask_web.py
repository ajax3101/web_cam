from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import face_recognition
import psycopg2

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = psycopg2.connect(database="mydatabase", user="myusername", password="mypassword", host="localhost", port="5432")
    cursor = conn.cursor()
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image = face_recognition.load_image_file(file_path)
            encoding = face_recognition.face_encodings(image)[0]
            name = request.form['name']
            cursor.execute("INSERT INTO faces (name, encoding) VALUES (%s, %s)", (name, encoding.tobytes()))
            conn.commit()
            return redirect(url_for('index'))
    cursor.execute("SELECT * FROM faces")
    faces = cursor.fetchall()
    return render_template('index.html', faces=faces)

if __name__ == '__main__':
    app.run(debug=True)
