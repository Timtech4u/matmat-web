from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView
from django.contrib.auth.views import logout

urlpatterns = patterns('questions.views',
    url(r'^play/$', "play", name="play"),
    url(r'^get_question/$', "get_question", name="get_question"),
    url(r'^get_question_test/$', "get_question_test",),
    url(r'^save_answer/$', "save_answer", name="save_answer"),
)