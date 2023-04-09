--Обратите внимание, что в таблице faces хранятся имена и кодировки лиц, а в таблице faces_log хранится 
--история обнаруженных лиц с указанием времени и ID соответствующей записи в таблице faces.
CREATE TABLE faces (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    encoding TEXT NOT NULL
);

CREATE TABLE faces_log (
    id SERIAL PRIMARY KEY,
    face_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL
);
