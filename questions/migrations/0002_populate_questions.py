# -*- coding: utf-8 -*-
from south.v2 import DataMigration
import json
import random


class Migration(DataMigration):

    def forwards(self, orm):
        # Simulators:
        # -----------
        free_answer = orm.Simulator(name='free_answer', note='Written answer')
        free_answer.save()
        counting = orm.Simulator(name='counting', note='Counting objects')
        counting.save()
        selecting = orm.Simulator(name='selecting',
                                  note='Selecting specified number of objects')
        selecting.save()
        numberline = orm.Simulator(name='numberline',
                                   note='Choose answer on number-line')
        numberline.save()
        fillin = orm.Simulator(name='fillin', note='Fill in written answer')
        fillin.save()
        field = orm.Simulator(name='field', note='2D field')
        field.save()
        example_sim = orm.Simulator(name='example', note='Just an example')
        example_sim.save()
        # Numbers:
        # --------
        for n in range(1, 101):
            skill = orm['model.Skill'].objects.get(name=str(n))
            # for numbers up to 7 ... choice up to 10
            # for numbers up to 17 ... choice up to 20
            # for numbers above .... choice up to a 100
            nr = 1 if n <= 7 else 2 if n <= 17 else 10
            # number -> select objects
            orm.Question(type='c', skill=skill, player=selecting,
                         data='{"question": %s, "answer": %s, "nrows": %s, '
                         '"ncols": 10}' % (n, n, nr)).save()
            # objects -> number
            orm.Question(type='c', skill=skill, player=counting,
                         data='{"question": [%s], "answer": "%s", '
                         '"width": 10}' % (n, n)).save()

        for n in range(1, 21):
            skill = orm['model.Skill'].objects.get(name=str(n))
            # number -> number-line
            orm.Question(type='c', skill=skill, player=numberline,
                         data='{{"question": "{0}", "answer": {0}}}'.
                         format(n)).save()

        skill = orm['model.Skill'].objects.get(name='numbers <= 10')
        for n in range(1, 11):
            pre = ', '.join(map(str, range(1, n)))
            pre = pre + ', ' if pre else ''
            post = ', '.join(map(str, range(n + 1, 11)))
            post = ', ' + post if post else ''
            orm.Question(
                type='c', skill=skill, player=fillin,
                data='{{"pre": "{0}", "post": "{1}", "answer": "{2}"}}'.
                format(pre, post, n)).save()

        # Addition:
        # ---------
        for a in range(1, 21):
            for b in range(1, 21):
                total = a + b
                if total <= 20:
                    x, y = (a, b) if a <= b else (b, a)
                    skill = orm['model.Skill'].objects.get(name='%s+%s' % (x, y))
                    orm.Question(type='c', skill=skill, player=free_answer,
                                 data='{"question": "%s + %s", "answer": "%s"}' % (a, b, total)).save()
                    orm.Question(type='c', skill=skill, player=counting,
                                 data='{"question": [%s, "+", %s], "answer": "%s", "width": 10}' % (a, b, total)).save()
        skill = orm['model.Skill'].objects.get(name='addition <= 100')
        random.seed(150 - 2)
        X = set([])
        while len(X) < 100:
            a, b = random.randint(1, 100), random.randint(1, 100)
            if (a > 20 or b > 20) and a + b <= 100:
                X.add((a, b))
        for a, b in X:
            total = a + b
            orm.Question(type='c', skill=skill, player=free_answer,
                         data='{"question": "%s + %s", "answer": "%s"}' % (a, b, total)).save()

        # Subtraction:
        # ------------
        skill = orm['model.Skill'].objects.get(name='subtraction')
        X = set([])
        # up to 20
        for a in range(21):
            for b in range(b, 21):
                X.add((a, b))
        # multiples of 5:
        for a in range(10, 101, 5):
            for b in range(a, 101, 5):
                X.add((a, b))
        # create the questions
        for a, b in X:
            total = a - b
            orm.Question(type='c', skill=skill, player=free_answer,
                         data='{"question": "%s - %s", "answer": "%s"}' % (a, b, total)).save()
        # Multiplication:
        # ---------------
        # fillin removed for now
        X = set([])
        for a in range(11):
            for b in range(21):
                X.add((a, b))
                X.add((b, a))
        for a, b in X:
            total = a * b
            x, y = (a, b) if a <= b else (b, a)
            skill = orm['model.Skill'].objects.get(name='%sx%s' % (x, y))
            orm.Question(type='c', skill=skill, player=free_answer,
                         data='{"question": "%s x %s", "answer": "%s"}' % (a, b, total)).save()
            if total and a <= 5 and b <= 5:
                orm.Question(type='c', skill=skill, player=counting,
                             data='{"question": [%s], "answer": "%s", '
                             '"width": %s}' % (total, total, b)).save()
        for a, b, x in MULTI_2D:
            a, b = (b, a) if b < a else (a, b)
            total = a * b
            skill = orm['model.Skill'].objects.get(name='%sx%s' % (a, b))
            f = []
            for _ in range(10):
                l = []
                for _ in range(10):
                    l.append(x % 2)
                    x /= 2
                f.append(l)
            orm.Question(type='c', skill=skill, player=field,
                         data=json.dumps({"field": f, "answer": total})).save()
        # Division:
        # ---------------
        for a in range(11):
            for b in range(1, 11):
                total = a * b
                skill = orm['model.Skill'].objects.get(name='%s/%s' % (total, b))
                orm.Question(type='c', skill=skill, player=free_answer,
                             data='{"question": "%s &divide; %s", "answer": "%s"}' % (total, b, a)).save()
        # division with modulo left out for now:
        '''
        skill = orm['model.Skill'].objects.get(name='division modulo')
        for a in range(1, 21):
            for b in range(1, 11):
                r = a / b
                m = a % b
                orm.Question(
                    type='c', skill=skill, player=fillin,
                    data=json.dumps({"pre": "%s &divide; %s = " % (a, b),
                                     "answer": str(r),
                                     "post": ", zbytek %s" % m})).save()
                orm.Question(
                    type='c', skill=skill, player=fillin,
                    data=json.dumps({"pre": "%s &divide; %s = %s, zbytek " % (a, b, r),
                                     "answer": str(m), "post": ""})).save()
        '''

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'model.skill': {
            'Meta': {'object_name': 'Skill'},
            'children_list': ('django.db.models.fields.TextField', [], {'default': "''"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['model.Skill']"})
        },
        u'questions.answer': {
            'Meta': {'object_name': 'Answer'},
            'correctly_solved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'answers'", 'to': u"orm['questions.Question']"}),
            'solving_time': ('django.db.models.fields.IntegerField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'questions.question': {
            'Meta': {'object_name': 'Question'},
            'data': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'player': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Simulator']"}),
            'skill': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['model.Skill']"}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'c'", 'max_length': '1'})
        },
        u'questions.simulator': {
            'Meta': {'object_name': 'Simulator'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['questions']
    symmetrical = True


MULTI_2D = [(2, 3, 464378630459495837192945664L),
            (2, 3, 154969178502272764675620864L),
            (2, 3, 19399481727942022140002304L),
            (2, 3, 9250393634619130048L),
            (2, 4, 237846639445326993806761918464L),
            (2, 4, 522596296501679744700383232L),
            (2, 4, 1154050703082184704),
            (2, 4, 1210109869999860540899712L),
            (2, 5, 28398762501475955605504L),
            (2, 5, 56723756044357137858560L),
            (2, 5, 103197707267),
            (2, 5, 6762826379034624),
            (2, 6, 13524005906553863),
            (2, 6, 585591890901659839365888L),
            (2, 6, 237839390765114558718656118784L),
            (2, 6, 865536385542520832),
            (2, 7, 79363694432322696471365296128L),
            (2, 7, 18150415576909756659794304L),
            (2, 7, 59479188147825424126571446272L),
            (2, 7, 34691363653860296015247055873L),
            (2, 8, 56733024449089315406720L),
            (2, 8, 8674049894688032821547630592L),
            (2, 8, 987465131315188186071695360L),
            (2, 8, 147718558587690156032L),
            (2, 9, 304682363115028642499923972L),
            (2, 9, 3717450145393953000652800000L),
            (2, 9, 116170326411259308691959820L),
            (2, 9, 1172253701416500877864960L),
            (3, 3, 36947531355908046848L),
            (3, 3, 56686844967458573385728L),
            (3, 3, 309938357075969254948343808L),
            (3, 3, 928757260927972451006033920L),
            (3, 4, 4646808619143783718374604800L),
            (3, 4, 3462142213541468550),
            (3, 4, 8265294341421051936768L),
            (3, 4, 591304616683836040195L),
            (3, 5, 1021034858408497012277248L),
            (3, 5, 110813328328115356416L),
            (3, 5, 886452521854656780487L),
            (3, 5, 69382675075476798420709015552L),
            (3, 6, 1110277472734076420174643214350L),
            (3, 6, 28365863076177750523904L),
            (3, 6, 14439454636081689919488L),
            (3, 6, 3630322692470583673160128L),
            (3, 7, 77688898305312845124390092800L),
            (3, 7, 9460890615527114808321L),
            (3, 7, 1110123636939686138349900279820L),
            (3, 7, 16174678326082803714L),
            (3, 8, 148697875812599391790619028600L),
            (3, 8, 237955558470537786965218951168L),
            (3, 8, 29080397365116556410642432L),
            (3, 8, 1148655708563897843810400L),
            (3, 9, 37213154579451933607712623616L),
            (3, 9, 9529597067742907248672768L),
            (3, 9, 2425090119965366057760798L),
            (3, 9, 7434900890320627811238773216L),
            (4, 3, 2586075837127003865472L),
            (4, 3, 18546035474477096984L),
            (4, 3, 158692673272890295464306409472L),
            (4, 3, 3956979490425608131854729216L),
            (4, 4, 3716240331543867246739734528L),
            (4, 4, 952596677225177017088114429964L),
            (4, 4, 29739575162519877710670300000L),
            (4, 4, 116177305945846605171922950L),
            (4, 5, 7261819491800848501279842L),
            (4, 5, 69382821976627382039747952640L),
            (4, 5, 554834101537442777870031151120L),
            (4, 5, 38756461872547194141179936L),
            (4, 6, 555138736399351044355624143872L),
            (4, 6, 237916828001447363422181548440L),
            (4, 6, 37145455840499914054498785286L),
            (4, 6, 475862698529040163205745219584L),
            (4, 7, 29739603518627664503577131983L),
            (4, 7, 277887333493740473167445522460L),
            (4, 7, 34734856649201615118892678144L),
            (4, 7, 281306162543337430033841488096L),
            (4, 8, 7551072093673635286981017600L),
            (4, 8, 513008125343372103545263721475L),
            (4, 8, 594791503527368931051622085100L),
            (4, 8, 36338645525283320469600L),
            (4, 9, 297707658032167120305033543680L),
            (4, 9, 1200390146272375434120052736L),
            (4, 9, 1152022401078339277449854976L),
            (4, 9, 533170408860181543374L),
            (5, 3, 9918027424121098496110548996L),
            (5, 3, 14172576133636260302976L),
            (5, 3, 10034160753607357188307681280L),
            (5, 3, 10861594026327776763794441267L),
            (5, 4, 237923862880329115745668300800L),
            (5, 4, 951673722562841630721290803200L),
            (5, 4, 39933625710277159110606904L),
            (5, 4, 929361723828749583797455875L),
            (5, 5, 7444565326430069261486984193L),
            (5, 5, 67729807305564197290557496L),
            (5, 5, 35606341081893953254574809112L),
            (5, 5, 7900181541687806630524190944L),
            (5, 6, 55833858385178948508L),
            (5, 6, 951667376891870199085128942016L),
            (5, 6, 475833655951025656129802608519L),
            (5, 6, 556648963003825955287349262L),
            (5, 7, 969016606987217309266826443968L),
            (5, 7, 33457053954561209852973050899L),
            (5, 7, 619879964961195617002823023L),
            (5, 7, 18296790934171505512206568448L)]
