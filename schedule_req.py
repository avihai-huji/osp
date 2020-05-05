from io import BytesIO
from urllib.parse import urlencode
import re
import pycurl
from bs4 import BeautifulSoup
import json


SERVER_URL = "https://shnaton.huji.ac.il/index.php"
CHARSET = 'windows-1255'
YEAR = '2020'


class ShnatonParser:

    LESSON_TABLE_CELL_NUM = 8  # number of <td>s in the lesson table rows

    @staticmethod
    def get_course_html(year, course_id):
        b_obj = BytesIO()
        crl = pycurl.Curl()

        data = {
            'peula': 'Simple',
            'maslul': '0',
            'shana': '0',
            'year': year,
            'course': course_id
        }
        pf = urlencode(data)

        crl.setopt(crl.URL, SERVER_URL)
        crl.setopt(crl.POSTFIELDS, pf)
        crl.setopt(crl.WRITEDATA, b_obj)
        crl.setopt(crl.CAINFO, './cacert.pem')

        crl.perform()
        crl.close()

        post_content = b_obj.getvalue()
        return post_content.decode(CHARSET)

    @staticmethod
    def parse_course(year, course_id):
        source = BeautifulSoup(
            ShnatonParser.get_course_html(year, course_id), 'html.parser')

        course = dict()
        # parse general course info
        ShnatonParser.parse_general_course_info(source, year, course)

        # parse lessons info
        ShnatonParser.parse_lessons(source, course)

        return course

    @staticmethod
    def parse_general_course_info(source, year, course):
        # get general course info elements
        general_course_info = source.find_all(class_='courseTD')

        course['id'] = re.sub("[^0-9]", "", general_course_info[2].string)
        course['name'] = general_course_info[1].string
        course['year'] = year
        course['semester'] = general_course_info[7].string
        course['nz'] = re.sub("[^0-9]", "", general_course_info[6].string)

    @staticmethod
    def parse_lessons(source, course):
        # get course lessons elements
        course_lessons = source.find_all(class_='courseDet')

        lessons = list()

        # the actual number of cells, without comment cells etc.
        actual_cell_num = len(course_lessons) - \
            (len(course_lessons) % ShnatonParser.LESSON_TABLE_CELL_NUM)

        for i in range(0, actual_cell_num,
                       ShnatonParser.LESSON_TABLE_CELL_NUM):
            lesson = dict()
            lesson['hall'] = ShnatonParser.parse_halls(course_lessons[i])
            lesson['hour'] = ShnatonParser.parse_hours(course_lessons[i + 2])
            lesson['day'] = ShnatonParser.parse_days(course_lessons[i + 3])
            lesson['semester'] = ShnatonParser.parse_semester(
                course_lessons[i + 4])
            lesson['group'] = course_lessons[i + 5].string
            lesson['type'] = course_lessons[i + 6].string
            lesson['lecturer'] = ShnatonParser.parse_lecturers(
                course_lessons[i + 7])

            lessons.append(lesson)

        course['lessons'] = lessons

    @staticmethod
    def parse_halls(halls):
        ret = list()
        hall_children = halls.find_all('b')

        for hall in hall_children:
            ret.append(hall.string)

        return ret

    @staticmethod
    def parse_hours(hours):
        ret = list()

        for hour in hours.contents:
            if hour.string is not None:
                # not <br>, append it
                ret.append(hour.string)

        return ret

    @staticmethod
    def parse_days(days):
        ret = list()

        for day in days.contents:
            if day.string is not None:
                # not <br>, append it
                ret.append(day.string)

        return ret

    @staticmethod
    def parse_semester(semesters):
        ret = list()

        for semester in semesters.contents:
            if semester.string is not None:
                # not <br>, append it
                ret.append(semester.string)

        return ret

    @staticmethod
    def parse_lecturers(lecturers):
        ret = list()

        for lecturer in lecturers.contents:
            if lecturer.string is not None:
                # not <br>, append it
                ret.append(lecturer.string)

        return ret


with open('./courses_2020.json', 'r', encoding='utf8') as f:
    course_list = json.loads(f.read())

    for course in course_list:
        parsed_course = ShnatonParser.parse_course(YEAR, course['id'])
        json_str = json.dumps(parsed_course, ensure_ascii=False)

        print(parsed_course)
        break  # remove if you want to iterate over all the courses


