from flask import Flask, render_template, request, send_file
from table import get_timetable
import pandas as pd
import io
import copy
import pprint

app = Flask(__name__)

timetable_global = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    csv_data = None
    inputs = []
    timetable_classes = {}
    timetable_teachers = {}

    if request.method == 'POST':
        inputs = request.form.getlist('input_field')
        initial_lectures = []

        for i in range(0, len(inputs), 3):
            temp = []
            temp.append(inputs[i])
            temp.append([int(x) for x in inputs[i + 1].split(',')])
            temp.append([int(x) for x in inputs[i + 2].split(',')])
            initial_lectures.append(temp)

        if 'csv_file' in request.files:
            file = request.files['csv_file']
            if file.filename != '':
                timetables = get_timetable(file, initial_lectures)
                if(timetables == []):
                    print("mistakes happened")
                    exit(0)
                timetable_classes, timetable_teachers = timetables
                print("done")
    
    zipped_timetable = {}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    clases = list(timetable_classes.keys())
    clases.sort()
    for class_name in clases:
        zipped_timetable[class_name] = list(zip(days, timetable_classes[class_name]))
    teachers = list(timetable_teachers.keys())
    teachers.sort()
    for proff_name in teachers:
        zipped_timetable[proff_name] = list(zip(days, timetable_teachers[proff_name]))
    global timetable_global
    timetable_global = copy.deepcopy(zipped_timetable)
    return render_template('index.html', csv_data=zipped_timetable, inputs=inputs)

@app.route('/download')
def download():
    global timetable_global
    if timetable_global:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for class_name, schedule in timetable_global.items():
                temp = []
                for i in range(0, 5):
                    temp.append([])
                    temp[i].append(schedule[i][0])
                    for j in schedule[i][1]:
                        temp[i].append(j)
                df = pd.DataFrame(temp, columns=['Day', 'Period 1', 'Period 2', 'Period 3', 'Period 4', 'Lunch', 'Period 5', 'Period 6', 'Period 7', 'Period 8'])
                df.to_excel(writer, index=False, sheet_name=class_name)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name='timetable.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        return "No timetable data available to download."

if __name__ == '__main__':
    app.run(debug=True)