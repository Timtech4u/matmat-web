import json
from collections import defaultdict
import os
from django.core.cache import cache
from clint.textui import progress
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.models.signals import post_save
from proso.django.config import get_global_config
from proso_common.models import Config
from proso_models.models import update_predictive_model, AnswerMeta
from proso_tasks.models import TaskInstance, TaskAnswer
from proso_user.models import UserProfile, Session


class Command(BaseCommand):
    help = 'Migrate from old matmat version'
    data_dir = 'data'

    def add_arguments(self, parser):
        parser.add_argument('parts', nargs='+', type=str)

    def handle(self, *args, **options):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        if 'flush' in options['parts']:
            call_command('flush')

        if 'users' in options['parts']:
            self.migrate_users()

        if 'profiles' in options['parts']:
            self.migrate_profiles()

        if 'questions' in options['parts']:
            self.migrate_question()

        if 'answers' in options['parts']:
            self.migrate_answers()

        cache.clear()

    def migrate_users(self):
        self.dump_load('auth', exclude=['auth.Permission'] )
        self.dump_load('lazysignup')
        self.dump_load('default', exclude=['default.Code'])

        self.stdout.write(self.style.SUCCESS('Users successfully migrated'))

    def migrate_profiles(self):
        profiles = {}
        with connections['old'].cursor() as cursor:
            cursor.execute('SELECT u.user_id, u.code, cp.user_id as child'
                           '  FROM core_userprofile u '
                           '  LEFT JOIN core_userprofile_children c '
                           '    ON u.id = c.from_userprofile_id'
                           '  LEFT JOIN core_userprofile cp '
                           '    ON c.to_userprofile_id = cp.id')
            for profile in dict_fetch_all(cursor):
                if profile['user_id'] in profiles:
                    profiles[profile['user_id']]['children'].append(profile['child'])
                else:
                    profiles[profile['user_id']] = {
                        'code': profile['code'],
                        'children': [] if profile['child'] is None else [profile['child']]
                    }
            with open('matmat-profiles.json', 'w') as output:
                json.dump(profiles, output)
            self.stdout.write(self.style.SUCCESS('Profiles successfully exported'))

        for user in User.objects.filter(lazyuser__isnull=True):
            UserProfile.objects.get_or_create(user=user)
        self.stdout.write(self.style.SUCCESS('New profiles successfully created'))

        self.stdout.write(self.style.ERROR('Profiles import not implemented!'))  # TODO

    def migrate_question(self):
        call_command('generate_tasks')
        call_command('load_tasks', os.path.join('data', 'matmat-contexts.json'),
                     os.path.join('data', 'matmat-skills.json'), os.path.join('data', 'matmat-tasks.json'))

    def dump_load(self, app, exclude=None):
        self.stdout.write('Copy ' + app)
        if exclude is None:
            exclude = []
        file_name = os.path.join(self.data_dir, 'matmat-{}.json'.format(app))
        with open(file_name, 'w') as output:
            self.stdout.write(' - dumping')
            call_command('dumpdata', app,
                         stdout=output,
                         exclude=exclude,
                         database='old'
                         )
        self.stdout.write(' - loading')
        call_command('loaddata', file_name)

    def migrate_answers(self):
        post_save.disconnect(update_predictive_model)

        Session.objects.all().delete()
        TaskAnswer.objects.all().delete()

        old_new_id_map = json.load(open('matmat/management/commands/old_new_id_map.json'))
        old_new_id_map = {k: v for k, v in old_new_id_map}
        task_instances = {t.identifier: t for t in TaskInstance.objects.all().select_related('task')}
        config = Config.objects.from_content(get_global_config()).id

        with connections['old'].cursor() as cursor:
            cursor.execute('SELECT '
                           '    a.timestamp, '
                           '    a.user_id, '
                           '    a.correctly_solved, '
                           '    a.solving_time, '
                           '    a.answer,'
                           '    a.device, '
                           '    q.identifier'
                           ' FROM questions_answer a '
                           ' LEFT JOIN questions_question q '
                           '    ON q.id = a.question_id '
                           ' WHERE q.active IS TRUE '
                           ' ORDER BY a.id'
                           )

            sessions = defaultdict(lambda: (None, None))
            metas = {}
            answers = []
            for answer in progress.bar(dict_fetch_all(cursor),
                                       every=max(1, min(100, cursor.rowcount // 1000)), expected_size=cursor.rowcount):
                user = answer['user_id']

                if answer['identifier'] not in old_new_id_map:
                    print('Question ID not found: ', answer['identifier'])

                task_instance = task_instances[old_new_id_map[answer['identifier']]]

                session, last_update = sessions[user]
                if session is None or (last_update is not None and (answer['timestamp'] - last_update) > timedelta(minutes=30)):
                    session = Session.objects.create(user_id=user)
                sessions[user] = session, answer['timestamp']

                device = answer['device']
                if device in metas:
                    meta = metas[device]
                else:
                    meta = AnswerMeta.objects.from_content({'device': device})
                    metas[device] = meta

                a = TaskAnswer(
                    user_id=user,
                    item_id=task_instance.item_id,
                    item_asked_id=task_instance.item_id,
                    item_answered_id=task_instance.item_id if answer['correctly_solved'] else None,
                    response_time=answer['solving_time'] * 1000,
                    lang='cs',
                    question=task_instance.task.identifier,
                    answer=answer['answer'],
                    session_id=session.pk,
                    config_id=config,
                    metainfo_id=meta.pk
                )
                answers.append(a)
                a.save()


def dict_fetch_all(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]
