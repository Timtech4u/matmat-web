from collections import defaultdict
from contextlib import closing
import csv
import zipfile

import sys
from django.db import connection
import os
from django.core.management import BaseCommand, CommandError
import re
from matmat import settings
from questions.models import Answer, Question, Simulator
from model.models import Skill
import pandas as pd
import json


class Command(BaseCommand):
    args = 'table name'
    help = "Export data"

    BATCH_SIZE = 5 * 10**5
    MODELS_TO_EXPORT = [Question, Answer, Simulator, Skill]

    def __init__(self):
        super(Command, self).__init__()
        self.tables_to_export = []
        for model in self.MODELS_TO_EXPORT:
            self.tables_to_export.append(model._meta.db_table)

    def handle(self, *args, **options):

        if len(args) > 0 and len(args) != 1:
            raise CommandError('''
                The command requires exactly one arguments:
                - table name
                or no argument.
            ''')

        if len(args) > 0:
            table_name = args[0]
            self.handle_one_table(table_name)
        else:
            self.handle_all_tables()

    def handle_all_tables(self):
        if not os.path.exists(os.path.join(settings.MEDIA_ROOT, "raw")):
            os.makedirs(os.path.join(settings.MEDIA_ROOT, "raw"))
        for table_name in self.tables_to_export:
            self.handle_one_table(table_name)

        prepare_data(input_dir=os.path.join(settings.MEDIA_ROOT, "raw"), output_dir=settings.MEDIA_ROOT)
        filename_zip = os.path.join(settings.MEDIA_ROOT, "matmat_export_raw.zip")
        files = [os.path.join(settings.MEDIA_ROOT, "raw", f + '.csv') for f in self.tables_to_export]
        zip_files(filename_zip, files)

        filename_zip = os.path.join(settings.MEDIA_ROOT, "matmat_export.zip")
        files = [os.path.join(settings.MEDIA_ROOT, f + '.csv') for f in ["answers", "items", "skills"]]
        zip_files(filename_zip, files)


    def handle_one_table(self, table_name):
        if table_name not in self.tables_to_export:
            raise CommandError('table "%s" is not supported' % table_name)

        count = 0
        with closing(connection.cursor()) as cursor:
            cursor.execute('SELECT COUNT(*) FROM ' + table_name)
            count, = cursor.fetchone()
        print 'processing %s' % table_name, ',', count, 'items'

        sql = 'SELECT * FROM ' + table_name
        filename_csv = settings.MEDIA_ROOT + '/raw/' + table_name + '.csv'
        for offset in xrange(0, count, self.BATCH_SIZE):
            with closing(connection.cursor()) as cursor:
                cursor.execute(sql + ' LIMIT ' + str(self.BATCH_SIZE) + ' OFFSET ' + str(offset))
                self.dump_cursor(
                    cursor,
                    filename_csv,
                    append=(offset > 0))

    def dump_cursor(self, cursor, filename, append=False):
        headers = [re.sub(r'_id$', '', col[0]) for col in cursor.description]
        with open(filename, 'a' if append else 'w') as csvfile:
            writer = csv.writer(csvfile)
            if not append:
                writer.writerow(headers)
            for row in cursor:
                row = [val.encode('utf-8') if isinstance(val, unicode) else val for val in row]
                writer.writerow(row)

def zip_files(filename_zip, files):
    if os.path.exists(filename_zip):
        os.remove(filename_zip)

    zf = zipfile.ZipFile(filename_zip, 'w', zipfile.ZIP_DEFLATED)
    for filename in files:
        zf.write(filename, os.path.basename(filename))
        # os.remove(filename)
    zf.close()

def get_skill_parents(skills):
    map = {}
    for id, skill in skills.iterrows():
        map[id] = int(skill["parent"]) if not pd.isnull(skill["parent"]) else None
    return map


def get_skill_parent_lists(skills):
    map = get_skill_parents(skills)
    lists = defaultdict(lambda: [])
    for skill in map:
        s = skill
        while s:
            lists[skill].append(s)
            s = map[s]
    return lists


def parse_question(item, data):
    if item["visualization"] == "pairing":
        return ""
    question = data["question"] if "question" in data else data["text"]
    if type(question) is list and len(question) == 3 and type(question[0]) is unicode:
        question = question[0]
    if type(question) is list and len(question) == 3 and type(question[0]) is int:
        question = "".join(map(str, question))
    if type(question) is list and len(question) == 1:
        question = question[0]
    question = str(question).replace("&times;", "x").replace("&divide;", "/").replace(" ", "")
    return question


def prepare_data(input_dir="data/source", output_dir="data"):
    csv.field_size_limit(sys.maxsize)
    answers = pd.read_csv(os.path.join(input_dir, "questions_answer.csv"), engine='python', index_col=0)
    items = pd.read_csv(os.path.join(input_dir, "questions_question.csv"), index_col=0)
    simulators = pd.read_csv(os.path.join(input_dir, "questions_simulator.csv"), index_col=0)
    skills = pd.read_csv(os.path.join(input_dir, "model_skill.csv"), index_col=0)
    skill_parents = get_skill_parent_lists(skills)

    items = items.join(simulators, "player")
    items.rename(inplace=True, columns={"name": "visualization"})
    items["answer"] = 0
    items["question"] = ""
    items["skill_lvl_1"], items["skill_lvl_2"], items["skill_lvl_3"] = None, None, None
    for id, item in items.iterrows():
        data = json.loads(item["data"])
        items.loc[id, "data"] = item["data"].replace('"', "'")
        items.loc[id, "answer"] = int(data["answer"]) if item["visualization"] != "pairing" else None
        items.loc[id, "question"] = parse_question(item, data)
        for i, skill in enumerate(skill_parents[item["skill"]][::-1][1:]):
            items.loc[id, "skill_lvl_{}".format(i + 1)] = skill
    items = items[["question", "answer", "visualization", "skill", "skill_lvl_1", "skill_lvl_2", "skill_lvl_3", "data"]]

    answers.rename(inplace=True, columns={
        "question": "item",
        "user": "student",
        "solving_time": "response_time",
        "correctly_solved": "correct",
    })
    answers = answers.join(items[["answer"]], on="item", rsuffix="_expected")
    answers = answers[["timestamp", "item", "student", "response_time", "correct", "answer", "answer_expected", "device", "log"]]
    answers = answers.round({"response_time": 3})

    skills.rename(inplace=True, columns={"note": "name_cz",})
    skills = skills[["name", "parent"]]

    simulators.rename(inplace=True, columns={"note": "name_cz",})

    answers.to_csv(os.path.join(output_dir, "answers.csv"))
    items.to_csv(os.path.join(output_dir, "items.csv"))
    # simulators.to_csv(os.path.join(output_dir, "visualizations.csv"))
    skills.to_csv(os.path.join(output_dir, "skills.csv"), float_format="%.0f")



