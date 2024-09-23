import io
import chardet
import os
import codecs
import csv
import sqlite3
filename = 'default.txt'
connection = sqlite3.connect('user_data.db', check_same_thread=False)

cursor = connection.cursor()
bytes = min(32, os.path.getsize(filename))
raw = open(filename, 'rb').read(bytes)

if raw.startswith(codecs.BOM_UTF8):
    encoding = 'utf-8-sig'
else:
    result = chardet.detect(raw)
    encoding = result['encoding']

infile = io.open(filename, 'r', encoding=encoding)
data = infile.read()
infile.close()
count = 0
data = data.split('\n')

for i in range(0, len(data), 2):
    term = data[i].split(' – ')[0]
    definition = data[i].split(' – ')[1]
    cursor.execute('INSERT INTO Terms (term, opr) VALUES (?, ?)',
                   (f"{str(term)}", f"{str(definition)}"))
    connection.commit()
    print([str(term), str(definition)])
