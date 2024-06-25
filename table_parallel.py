import pandas as pd
import random
import time
import pprint
import copy
import concurrent.futures

class TimetableProcessor:
    def __init__(self, timetable_classes, timetable_teachers, class_to_subj, total_hours_teacher, clas_teacher):
        self.read_only_timetable_classes = timetable_classes
        self.read_only_timetable_teachers = timetable_teachers
        self.read_only_class_to_subj = class_to_subj
        self.read_only_total_hours_teacher = total_hours_teacher
        self.timetable_classes = None
        self.timetable_teachers = None
        self.check = False
        self.clas_teacher = copy.deepcopy(clas_teacher)

    def worker(self):
        timetable_classes_temp = self.read_only_timetable_classes
        timetable_teachers_temp = self.read_only_timetable_teachers
        class_to_subj_temp_1 = self.read_only_class_to_subj
        class_to_subj_temp_2 = self.read_only_class_to_subj
        total_hours_teacher_temp = self.read_only_total_hours_teacher
        clas_teacher_temp = self.clas_teacher
        add_classes(timetable_classes_temp, timetable_teachers_temp, class_to_subj_temp_1, total_hours_teacher_temp)
        update_classes(timetable_classes_temp, timetable_teachers_temp, class_to_subj_temp_2, class_to_subj_temp_1, total_hours_teacher_temp, self.read_only_timetable_classes)
        proff_temp = copy.deepcopy(timetable_teachers_temp)
        check_temp = verify_all(timetable_classes_temp, proff_temp, class_to_subj_temp_2, clas_teacher_temp)
        print(check_temp)
        return check_temp, timetable_classes_temp, timetable_teachers_temp

    def process_timetable(self):
        while not self.check:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.worker) for _ in range(100)]
                for future in concurrent.futures.as_completed(futures):
                    check, temp_classes, temp_teachers = future.result()
                    if check:
                        print("DONE!!", check)
                        self.timetable_classes = temp_classes
                        self.timetable_teachers = temp_teachers
                        self.check = True
                        break
        return [self.timetable_classes, self.timetable_teachers]

def make_random():
    current_time_ns = time.time_ns()
    random.seed(current_time_ns)
    return int((random.random() * 100000000) // 1)
    
def extract_teacher_and_class_schedules(file_path):
    df = pd.read_excel(file_path)
    df.columns = df.iloc[0]
    df = df[1:]
    df.reset_index(drop=True, inplace=True)
    classes = df.columns[2:]

    teacher_schedule = {}
    class_schedule = {class_name: [] for class_name in classes}

    for _, row in df.iterrows():
        teacher_name = row['NAME']
        if pd.notna(teacher_name):
            teacher_schedule[teacher_name] = {}
            for class_name in classes:
                periods = row[class_name]
                if pd.notna(periods):
                    teacher_schedule[teacher_name][class_name] = str(periods)
                    class_schedule[class_name].append((teacher_name, periods))
    
    return teacher_schedule, class_schedule

def extract_class_teacher_and_clean_schedule(teacher_schedule):
    clas_teacher = {}
    for teacher, classes in teacher_schedule.items():
        if 'NAME' in classes:
            del teacher_schedule[teacher]['NAME']
        if 'TOTAL PERIOD' in classes:
            del teacher_schedule[teacher]['TOTAL PERIOD']
        for clas, periods in list(classes.items()):
            if clas == "Cl.Tr. And Subject":
                clas_teacher[periods] = teacher
                del teacher_schedule[teacher][clas]
                break
        for clas, periods in classes.items():
            temp = periods.split(' ')
            temp = list(filter(lambda a: a != '', temp))
            teacher_schedule[teacher][clas] = [x.split('-') for x in temp]
    return clas_teacher

def map_classes_to_subjects(clas_teacher, teacher_schedule):
    class_to_subj = {clas: [] for clas in clas_teacher.keys()}

    for teacher, classes in teacher_schedule.items():
        for clas, periods in classes.items():
            for period in periods:
                class_to_subj[clas].append([period[0], teacher, int(period[1])])

    return class_to_subj

def initilisation(class_to_subj, teacher_schedule):
    timetable_classes = {clas: [["Lunch" if i == 4 else "" for i in range(9)] for _ in range(5)] for clas in class_to_subj.keys()}
    timetable_teachers = {teach: [["Lunch" if i == 4 else "" for i in range(9)] for _ in range(5)] for teach in teacher_schedule.keys()}
    return timetable_classes, timetable_teachers

def is_available_teacher(timetable_teachers, teacher, day, period, total_hours_teacher):
    if teacher in total_hours_teacher.keys():
        count = sum(1 for i in range(9) if isinstance(timetable_teachers[teacher][day][i], list))
        return timetable_teachers[teacher][day][period] == "" and count < 7
    count = sum(1 for i in range(9) if isinstance(timetable_teachers[teacher][day][i], list))
    return timetable_teachers[teacher][day][period] == "" and count < 6

def add_initials(initial_classes, timetable_classes, timetable_teachers, teacher_to_subj, total_hours_teacher, class_to_subj):
    random.shuffle(initial_classes)
    for ini in initial_classes:
        if ini[0] not in timetable_teachers.keys():
            return 0
        slots = [[x, y] for x in ini[1] for y in ini[2]]
        total = 0
        for subj in teacher_to_subj[ini[0]]:
            total += subj[2]
        if(total > len(slots)):
            return 1
        if(total / len(ini[1]) > 6):
            total_hours_teacher[ini[0]] = total*5
        while(len(teacher_to_subj[ini[0]]) != 0):
            possibles = []
            for subj in teacher_to_subj[ini[0]]:
                for slot in slots:
                    if(timetable_classes[subj[1]][slot[0]][slot[1]] == "" and is_available_teacher(timetable_teachers, ini[0], slot[0], slot[1], total_hours_teacher)):
                        possibles.append([subj, slot])
            if(len(possibles) == 0):
                return 3
            select = possibles[make_random() % len(possibles)]
            choice = select[0]
            slot = select[1]
            slots.remove(slot)
            timetable_classes[choice[1]][slot[0]][slot[1]] = [choice[0], ini[0]]
            timetable_teachers[ini[0]][slot[0]][slot[1]] = [choice[0], choice[1]]
            for subj in teacher_to_subj[ini[0]]:
                if subj[0] == choice[0] and subj[1] == choice[1]:
                    subj[2]-=1
                    if(subj[2] == 0):
                        teacher_to_subj[ini[0]].remove(subj)
            for subj in class_to_subj[choice[1]]:
                if(subj[0] == choice[0] and subj[1] == ini[0]):
                    subj[2] -= 1
                    if(subj[2] == 0):
                        class_to_subj[choice[1]].remove(subj)
                    break
    return 2

def add_class_teacher_classes(timetable_teachers, timetable_classes, class_to_subj, clas_teacher):
    for clas, teacher in clas_teacher.items():
        if clas == "PREKG":
            for day in range(5):
                for period in range(4):
                    timetable_classes[clas][day][period] = [class_to_subj[clas][0][0], class_to_subj[clas][0][1]]
                    timetable_teachers[teacher][day][period] = [class_to_subj[clas][0][0], clas]
            class_to_subj[clas].pop(0)
            continue
        for sub in class_to_subj[clas]:
            if sub[1] == teacher and sub[2] > 4:
                for day in range(5):
                    timetable_classes[clas][day][0] = [sub[0], sub[1]]
                    timetable_teachers[sub[1]][day][0] = [sub[0], clas]
                    sub[2] -= 1
                    if sub[2] == 0:
                        class_to_subj[clas].remove(sub)
                break

def add_classes(timetable_classes, timetable_teachers, class_to_subj, total_hours_teacher):
    classes = list(timetable_classes.keys())
    for clas in classes:
        for day in range(5):
            for period in range(9):
                if timetable_classes[clas][day][period] != "":
                    continue
                possibles = [
                    course for course in class_to_subj[clas]
                    if is_available_teacher(timetable_teachers, course[1], day, period, total_hours_teacher)
                ]
                if not possibles:
                    continue
                choice = random.choice(possibles)
                timetable_classes[clas][day][period] = [choice[0], choice[1]]
                timetable_teachers[choice[1]][day][period] = [choice[0], clas]
                choice[2] -= 1
                if choice[2] == 0:
                    class_to_subj[clas].remove(choice)

def update_classes(timetable_classes, timetable_teachers, class_to_subj, class_to_subj_temp, total_hours_teacher, timetable_classes_original):
    for clas in timetable_classes.keys():
        for day in range(0,5):
            for period in range(0, 9):
                if(timetable_classes[clas][day][period] == ""):
                    possibles = []
                    for subject in class_to_subj[clas]:
                        if(is_available_teacher(timetable_teachers, subject[1], day, period, total_hours_teacher)):
                            possibles.append(subject)
                    if possibles == []:
                        return
                    replaceable = []
                    for pos in possibles:
                        for i in range(0,5):
                            for j in range(0,9):
                                if(type(timetable_teachers[pos[1]][i][j]) == str):
                                    continue
                                if(timetable_classes_original[clas][i][j] != ""):
                                    continue
                                if(timetable_teachers[pos[1]][i][j][1] == clas and timetable_teachers[pos[1]][i][j][0] == pos[0]):
                                    for subject in class_to_subj_temp[clas]:
                                        if(is_available_teacher(timetable_teachers, subject[1], i, j, total_hours_teacher)):
                                            replaceable.append([pos, subject, i, j])
                    if replaceable == []:
                        return
                    choice = random.choice(replaceable)
                    timetable_classes[clas][day][period] = [choice[0][0], choice[0][1]]
                    timetable_classes[clas][choice[2]][choice[3]] = [choice[1][0], choice[1][1]]
                    timetable_teachers[choice[0][1]][day][period] = [choice[0][0], clas]
                    timetable_teachers[choice[0][1]][choice[2]][choice[3]] = ""
                    timetable_teachers[choice[1][1]][choice[2]][choice[3]] = [choice[1][0], clas]
                    for subject in class_to_subj_temp[clas]:
                        if(subject[0] == choice[1][0] and subject[1] == choice[1][1]):
                            subject[2] -= 1
                            if subject[2] == 0:
                                class_to_subj_temp[clas].remove(subject)
                            break

def get_exceptions(teacher_schedule):
    temp = {}
    for teach in teacher_schedule.keys():
        total = 0
        for clas in teacher_schedule[teach].keys():
            for period in teacher_schedule[teach][clas]:
                total += int(period[1])
        if(total > 30):
            temp[teach] = total
    return temp

def check_is_full(class_to_subj):
    return all(not val for val in class_to_subj.values())

def verify_all(timetable_classes, timetable_teachers, class_to_subj, clas_teacher):
    for clas in timetable_classes.keys():
        for day in range(5):
            for period in range(9):
                if timetable_classes[clas][day][period] == "":
                    if clas == "PREKG":
                        continue
                    return False
                if timetable_classes[clas][day][period] == "Lunch":
                    continue
                if period == 0:
                    if timetable_classes[clas][day][period][1] != clas_teacher[clas]:
                        return False
                    else:
                        timetable_teachers[clas_teacher[clas]][day][period] = ""
                        for subject in class_to_subj[clas]:
                            if subject[0] == timetable_classes[clas][day][period][0] and subject[1] == timetable_classes[clas][day][period][1]:
                                subject[2] -= 1
                                if subject[2] == 0:
                                    class_to_subj[clas].remove(subject)
                                break
                else:
                    if timetable_classes[clas][day][period][0] != timetable_teachers[timetable_classes[clas][day][period][1]][day][period][0] or \
                       timetable_teachers[timetable_classes[clas][day][period][1]][day][period][1] != clas:
                        return False
                    else:
                        timetable_teachers[timetable_classes[clas][day][period][1]][day][period] = ""
                        for subject in class_to_subj[clas]:
                            if subject[0] == timetable_classes[clas][day][period][0] and subject[1] == timetable_classes[clas][day][period][1]:
                                subject[2] -= 1
                                if subject[2] == 0:
                                    class_to_subj[clas].remove(subject)
                                break

    for teacher in timetable_teachers.keys():
        for day in range(5):
            for period in range(9):
                if timetable_teachers[teacher][day][period] != "" and timetable_teachers[teacher][day][period] != "Lunch":
                    return False

    for clas in class_to_subj.keys():
        if class_to_subj[clas]:
            return False
    
    return True

def transform_class_subjects(class_subjects):
    teacher_courses = {}

    for clas, subjects in class_subjects.items():
        for course in subjects:
            course_code, teacher, hours = course
            if teacher not in teacher_courses:
                teacher_courses[teacher] = []
            teacher_courses[teacher].append([course_code, clas, hours])

    return teacher_courses

def get_timetable(file_path, initial_classes):
    teacher_schedule, class_schedule = extract_teacher_and_class_schedules(file_path)
    clas_teacher = extract_class_teacher_and_clean_schedule(teacher_schedule)
    class_to_subj = map_classes_to_subjects(clas_teacher, teacher_schedule)
    teacher_to_subj = transform_class_subjects(class_to_subj)
    total_hours_teacher = get_exceptions(teacher_schedule)
    timetable_classes, timetable_teachers = initilisation(class_to_subj, teacher_schedule)
    add_class_teacher_classes(timetable_teachers, timetable_classes, class_to_subj, clas_teacher)
    result = 0
    fallback = 0
    while(result != 2 and fallback < 100):
        timetable_classes_temp = copy.deepcopy(timetable_classes)
        timetable_teachers_temp = copy.deepcopy(timetable_teachers)
        class_to_subj_temp_3 = copy.deepcopy(class_to_subj)
        teacher_to_subj_temp = copy.deepcopy(teacher_to_subj)
        result = add_initials(initial_classes, timetable_classes_temp, timetable_teachers_temp, teacher_to_subj_temp, total_hours_teacher, class_to_subj_temp_3)
        fallback += 1
        print(result)
        if(result == 2):
            timetable_classes = copy.deepcopy(timetable_classes_temp)
            timetable_teachers = copy.deepcopy(timetable_teachers_temp)
            class_to_subj = copy.deepcopy(class_to_subj_temp_3)
    if(result != 2):
        return []

    processor = TimetableProcessor(timetable_classes, timetable_teachers, class_to_subj, total_hours_teacher, clas_teacher)
    result = processor.process_timetable()
    print(result)