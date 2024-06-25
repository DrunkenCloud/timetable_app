import pandas as pd
import random
import time
import pprint
import copy

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

    for teacher, schedule in timetable_teachers.items():
        for day in range(5):
            for period in range(9):
                if schedule[day][period] not in ("", "Lunch"):
                    subject, class_name = schedule[day][period]
                    timetable_classes[class_name][day][period] = [subject, teacher]

    return timetable_classes, timetable_teachers

def add_classes_trash(timetable_classes, timetable_teachers, class_to_subj, total_hours_teacher, clas, overworked):
    for day in range(5):
        for period in range(9):
            if timetable_classes[clas][day][period] != "":
                continue
            possibles = [
                course for course in class_to_subj[clas]
                if is_available_teacher(timetable_teachers, course[1], day, period, total_hours_teacher) and
                is_clas_valid(clas, timetable_classes, timetable_teachers, class_to_subj, course, day, period, overworked) >= 0 and
                is_enough_slots(clas, timetable_classes, timetable_teachers, class_to_subj, course, day, period, overworked) and
                is_teacher_valid(timetable_teachers, course, day, period, class_to_subj, total_hours_teacher, overworked)
            ]
            if not possibles:
                continue
            choice = random.choice(possibles)
            timetable_classes[clas][day][period] = [choice[0], choice[1]]
            timetable_teachers[choice[1]][day][period] = [choice[0], clas]
            choice[2] -= 1
            if choice[2] == 0:
                class_to_subj[clas].remove(choice)

def update_classes_trash(timetable_classes, clas, timetable_teachers, class_to_subj, class_to_subj_temp, total_hours_teacher, timetable_classes_original):
    for day in range(0,5):
        for period in range(0, 9):
            if(timetable_classes[clas][day][period] == ""):
                possibles = []
                for subject in class_to_subj[clas]:
                    if(is_available_teacher(timetable_teachers, subject[1], day, period, total_hours_teacher)):
                        possibles.append(subject)
                if possibles == []:
                    continue
                replaceable = []
                for pos in possibles:
                    for i in range(0,5):
                        for j in range(0,9):
                            if(type(timetable_teachers[pos[1]][i][j]) == str or j == 0):
                                continue
                            if(timetable_teachers[pos[1]][i][j][1] == clas and timetable_teachers[pos[1]][i][j][0] == pos[0] and timetable_classes_original[clas][i][j] == ""):
                                for subject in class_to_subj_temp[clas]:
                                    if(is_available_teacher(timetable_teachers, subject[1], i, j, total_hours_teacher)):
                                        replaceable.append([pos, subject, i, j])
                if replaceable == []:
                    continue
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

def is_available_teacher(timetable_teachers, teacher, day, period, overworked):
    if overworked[teacher] == True:
        count = sum(1 for i in range(9) if isinstance(timetable_teachers[teacher][day][i], list))
        return timetable_teachers[teacher][day][period] == "" and count < 7
    count = sum(1 for i in range(9) if isinstance(timetable_teachers[teacher][day][i], list))
    return timetable_teachers[teacher][day][period] == "" and count < 6

def is_available_teacher_temp(timetable_teachers, teacher, day, period, total_hours_teacher):
    count = sum(1 for i in range(9) if isinstance(timetable_teachers[teacher][day][i], list))

def add_initials(initial_classes, timetable_classes, timetable_teachers, teacher_to_subj, total_hours_teacher, class_to_subj, overworked):
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
            overworked[ini[0]] = True
        while(len(teacher_to_subj[ini[0]]) != 0):
            possibles = []
            for subj in teacher_to_subj[ini[0]]:
                for slot in slots:
                    if(timetable_classes[subj[1]][slot[0]][slot[1]] == "" and is_available_teacher(timetable_teachers, ini[0], slot[0], slot[1], overworked)):
                        possibles.append([subj, slot])
            if(len(possibles) == 0):
                return 3
            select = possibles[make_random() % len(possibles)]
            choice = select[0]
            slot = select[1]
            slots.remove(slot)
            timetable_classes[choice[1]][slot[0]][slot[1]] = [choice[0], ini[0]]
            timetable_teachers[ini[0]][slot[0]][slot[1]] = [choice[0], choice[1]]
            total_hours_teacher[ini[0]] -= 1
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

def add_class_teacher_classes(timetable_teachers, timetable_classes, class_to_subj, clas_teacher, total_hours_teacher):
    for clas, teacher in clas_teacher.items():
        if clas == "PREKG":
            for day in range(5):
                for period in range(4):
                    timetable_classes[clas][day][period] = [class_to_subj[clas][0][0], class_to_subj[clas][0][1]]
                    timetable_teachers[teacher][day][period] = [class_to_subj[clas][0][0], clas]
                    total_hours_teacher[teacher] -= 1
            class_to_subj[clas].pop(0)
            continue
        for sub in class_to_subj[clas]:
            if sub[1] == teacher and sub[2] > 4:
                for day in range(5):
                    timetable_classes[clas][day][0] = [sub[0], sub[1]]
                    timetable_teachers[teacher][day][0] = [sub[0], clas]
                    total_hours_teacher[teacher] -= 1
                    sub[2] -= 1
                    if sub[2] == 0:
                        class_to_subj[clas].remove(sub)
                break

def get_total_hours(teacher_schedule):
    temp = {}
    over = {}
    for teach in teacher_schedule.keys():
        total = 0
        for clas in teacher_schedule[teach].keys():
            for period in teacher_schedule[teach][clas]:
                total += int(period[1])
        over[teach] = False
        if(total > 30 or teach in ['D.K', 'M.Ab', 'S.I', 'G.J', 'K.S.S', 'B.Re', 'P.S', 'H.R']):
            over[teach] = True
        temp[teach] = total
    return [temp, over]

def check_is_full(class_to_subj):
    return all(not val for val in class_to_subj.values())

def get_no_of_slots(timetable_teachers, teacher, day, period, overworked):
    timetable_teachers_temp = copy.deepcopy(timetable_teachers)
    count = 0
    if(day > 4):
        return count
    for i in range(day, day + 1):
        for j in range(period, 9):
            if is_available_teacher(timetable_teachers_temp, teacher, i, j, overworked):
                timetable_teachers_temp[teacher][i][j] = ["1"]
                count += 1
    
    for i in range(day + 1, 5):
        for j in range(0, 9):
            if is_available_teacher(timetable_teachers_temp, teacher, i, j, overworked):
                timetable_teachers_temp[teacher][i][j] = ["1"]
                count += 1
    return count

def get_conditions(clas, timetable_teachers, class_to_subj, day, period, overworked):
    temp = {}
    for subj in class_to_subj[clas]:
        if(subj[1] in temp):
            temp[subj[1]][1] += int(subj[2])
        else:
            temp[subj[1]] = [get_no_of_slots(timetable_teachers, subj[1], day, period, overworked), int(subj[2])]
    return temp

def is_enough_slots(clas, timetable_classes, timetable_teachers, class_to_subj, subj, day, period, overworked):
    class_to_subj_temp = copy.deepcopy(class_to_subj)
    timetable_classes_temp = copy.deepcopy(timetable_classes)
    timetable_teachers_temp = copy.deepcopy(timetable_teachers)

    timetable_classes_temp[clas][day][period] = [subj[0], subj[1]]
    timetable_teachers_temp[subj[1]][day][period] = [subj[0], clas]
    for course in class_to_subj_temp[clas]:
        if subj[0] == course[0] and subj[1] == course[1]:
            course[2] -= 1
            if course[2] == 0:
                class_to_subj_temp[clas].remove(course)
    if period == 8 and day == 4:
        return True
    elif period == 8:
        day += 1
        period = 0
    else:
        period += 1
    teacher_map_something = {}
    for something in class_to_subj[clas]:
        if(something[1] in teacher_map_something.keys()):
            teacher_map_something[something[1]][1] += int(something[2])
        else:
            teacher_map_something[something[1]] = [0, int(something[2])]
    hopefully_final_check = {}
    for i in range(day, day + 1):
        for j in range(period, 9):
            temp = []
            if(timetable_classes_temp[clas][i][j] != ""):
                continue
            for course in class_to_subj_temp[clas]:
                if(is_available_teacher(timetable_teachers, course[1], i, j, overworked)):
                    temp.append(course[1])
            if temp == []:
                return False
            if len(temp) == 1:
                if(teacher_map_something[temp[0]][0] == teacher_map_something[temp[0]][1]):
                    return False
                else:
                    teacher_map_something[temp[0]][0] += 1
                hopefully_final_check[str(i) + str(j)] = temp
    for i in range(day + 1, 5):
        for j in range(0, 9):
            temp = []
            if(timetable_classes_temp[clas][i][j] != ""):
                continue
            for course in class_to_subj_temp[clas]:
                if(is_available_teacher(timetable_teachers, course[1], i, j, overworked)):
                    temp.append(course[1])
            if temp == []:
                return False
            if len(temp) == 1:
                if(teacher_map_something[temp[0]][0] == teacher_map_something[temp[0]][1]):
                    return False
                else:
                    teacher_map_something[temp[0]][0] += 1
                hopefully_final_check[str(i) + str(j)] = temp
    for slot1 in hopefully_final_check.keys():
        another_temp = {}
        for slot2 in hopefully_final_check.keys():
            if slot1 == slot2:
                continue
            for teach in hopefully_final_check[slot2]:
                if teach in another_temp.keys():
                    another_temp[teach] += 1
                else:
                    another_temp[teach] = 1
        failure_counter = 0
        for teach in another_temp.keys():
            if(another_temp[teach] < teacher_map_something[teach][1]):
                failure_counter += 1
        if(failure_counter > 1):
            return False
    return True

def is_clas_valid(clas, timetable_classes, timetable_teachers, class_to_subj, subj, day, period, overworked):
    class_to_subj_temp = copy.deepcopy(class_to_subj)
    timetable_classes_temp = copy.deepcopy(timetable_classes)
    timetable_teachers_temp = copy.deepcopy(timetable_teachers)

    timetable_classes_temp[clas][day][period] = [subj[0], subj[1]]
    timetable_teachers_temp[subj[1]][day][period] = [subj[0], clas]
    if period == 8 and day == 4:
        return 1
    elif period == 8:
        day += 1
        period = 0
    else:
        period += 1

    for course in class_to_subj_temp[clas]:
        if subj[0] == course[0] and subj[1] == course[1]:
            course[2] -= 1
    current_conditions = get_conditions(clas, timetable_teachers_temp, class_to_subj_temp, day, period, overworked)
    if(current_conditions == {}):
        return 0
    min_t = current_conditions[subj[1]][0] - current_conditions[subj[1]][1]
    for val in current_conditions.values():
        if(val[0]-val[1] < min_t):
            min_t = val[0]-val[1]
    return min_t

def is_teacher_valid(timetable_teachers, subj, day, period, class_to_subj, total_hours_teacher, overworked):
    timetable_teachers_temp = copy.deepcopy(timetable_teachers)
    timetable_teachers_temp[subj[1]][day][period] = ["clas", subj[0]]
    poss_slot_count = get_no_of_slots(timetable_teachers_temp, subj[1], 0, 0, overworked)
    return poss_slot_count > (total_hours_teacher[subj[1]] - 1)

def add_classes(timetable_classes, clas, timetable_teachers, class_to_subj, teacher_to_subj, total_hours_teacher, overworked):
    for day in range(0, 5):
        for period in range(0, 9):
            if(timetable_classes[clas][day][period] != ""):
                continue
            possibles = []
            for subj in class_to_subj[clas]:
                is_available_teacher_temp(timetable_teachers, subj[1], day, period, total_hours_teacher)
                if(is_available_teacher(timetable_teachers, subj[1], day, period, overworked)):
                    min_t = is_clas_valid(clas, timetable_classes, timetable_teachers, class_to_subj, subj, day, period, overworked)
                    if(min_t >= 0):
                        if(is_enough_slots(clas, timetable_classes, timetable_teachers, class_to_subj, subj, day, period, overworked)):
                            if(is_teacher_valid(timetable_teachers, subj, day, period, class_to_subj, total_hours_teacher, overworked)):
                                possibles.append([subj, min_t])
            if possibles == []:
                print(day, period)
                return
            choice = possibles[0][0]
            min_t = possibles[0][1]
            finals = []
            for poss in possibles:
                if poss[1] > min_t:
                    min_t = poss[1]
                    finals = []
                    finals.append(poss)
                elif poss[1] == min_t:
                    finals.append(poss)
            final_choice = random.choice(finals)
            choice = final_choice[0]
            timetable_classes[clas][day][period] = [choice[0], choice[1]]
            timetable_teachers[choice[1]][day][period] = [choice[0], clas]
            total_hours_teacher[choice[1]] -= 1
            choice[2] -= 1
            if(choice[2] == 0):
                class_to_subj[clas].remove(choice)
            for course in teacher_to_subj[choice[1]]:
                if(course[0] == choice[0] and clas == course[1]):
                    course[2] -= 1
                    if course[2] == 0:
                        teacher_to_subj[choice[1]].remove(course)
                    break

def transform_class_subjects(class_subjects):
    teacher_courses = {}

    for clas, subjects in class_subjects.items():
        for course in subjects:
            course_code, teacher, hours = course
            if teacher not in teacher_courses:
                teacher_courses[teacher] = []
            teacher_courses[teacher].append([course_code, clas, hours])

    return teacher_courses

def make_timetables(timetable_classes, timetable_teachers, class_to_subj, teacher_to_subj, total_hours_teacher, overworked, initial_classes):
    classes = list(timetable_classes.keys())
    for clas in classes:
        check = False
        trys = 1
        while(check == False):
            timetable_classes_temp = copy.deepcopy(timetable_classes)
            timetable_teachers_temp = copy.deepcopy(timetable_teachers)
            class_to_subj_temp = copy.deepcopy(class_to_subj)
            teacher_to_subj_temp = copy.deepcopy(teacher_to_subj)
            total_hours_teacher_temp = copy.deepcopy(total_hours_teacher)
            add_classes(timetable_classes_temp, clas, timetable_teachers_temp, class_to_subj_temp, teacher_to_subj_temp, total_hours_teacher_temp, overworked)
            trys += 1
            print(clas, " Try: ", trys)
            print(class_to_subj_temp[clas])
            if(trys >= 100):
                return False, {}, {}
            if(class_to_subj_temp[clas] == []):
                check = True
                timetable_classes = copy.deepcopy(timetable_classes_temp)
                timetable_teachers = copy.deepcopy(timetable_teachers_temp)
                class_to_subj = copy.deepcopy(class_to_subj_temp)
                teacher_to_subj = copy.deepcopy(teacher_to_subj_temp)
                total_hours_teacher = copy.deepcopy(total_hours_teacher_temp)
    temp1 = copy.deepcopy(timetable_classes)
    temp2 = copy.deepcopy(timetable_teachers)
    return True, temp1, temp2

def stringle(timetable_classes, timetable_teachers):
    for clas in timetable_classes.keys():
        for day in range(0, 5):
            for period in range(0, 9):
                print(timetable_classes[clas][day][period])
                if(isinstance(timetable_classes[clas][day][period], list)):
                    timetable_classes[clas][day][period] = ' - '.join(timetable_classes[clas][day][period][::-1])
                print(timetable_classes[clas][day][period])
    
    for teach in timetable_teachers.keys():
        for day in range(0, 5):
            for period in range(0, 9):
                if(isinstance(timetable_teachers[teach][day][period], list)):
                    timetable_teachers[teach][day][period] = ' '.join(timetable_teachers[teach][day][period][::-1])

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

def get_timetable(file_path, initial_classes):
    teacher_schedule, class_schedule = extract_teacher_and_class_schedules(file_path)
    clas_teacher = extract_class_teacher_and_clean_schedule(teacher_schedule)
    class_to_subj = map_classes_to_subjects(clas_teacher, teacher_schedule)
    teacher_to_subj = transform_class_subjects(class_to_subj)
    total_hours_teacher, overworked = get_total_hours(teacher_schedule)
    timetable_classes, timetable_teachers = initilisation(class_to_subj, teacher_schedule)
    add_class_teacher_classes(timetable_teachers, timetable_classes, class_to_subj, clas_teacher, total_hours_teacher)
    result = 0
    fallback = 0
    while(result != 2 and fallback < 100):
        timetable_classes_temp = copy.deepcopy(timetable_classes)
        timetable_teachers_temp = copy.deepcopy(timetable_teachers)
        class_to_subj_temp = copy.deepcopy(class_to_subj)
        teacher_to_subj_temp = copy.deepcopy(teacher_to_subj)
        total_hours_teacher_temp = copy.deepcopy(total_hours_teacher)
        result = add_initials(initial_classes, timetable_classes_temp, timetable_teachers_temp, teacher_to_subj_temp, total_hours_teacher_temp, class_to_subj_temp, overworked)
        fallback += 1
        if(result == 2):
            timetable_classes = copy.deepcopy(timetable_classes_temp)
            timetable_teachers = copy.deepcopy(timetable_teachers_temp)
            class_to_subj = copy.deepcopy(class_to_subj_temp)
            total_hours_teacher = copy.deepcopy(total_hours_teacher_temp)
    check = False
    fallback = 0
    temp1 = {}
    temp2 = {}
    while(check == False and fallback < 100):
        check, temp1, temp2 = make_timetables(timetable_classes, timetable_teachers, class_to_subj, teacher_to_subj, total_hours_teacher, overworked)
        fallback += 1
    temp3 = copy.deepcopy(temp2)
    check = verify_all(temp1, temp2, class_to_subj, clas_teacher)
    stringle(temp1, temp3)
    return temp1, temp2