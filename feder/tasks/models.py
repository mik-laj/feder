from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from model_utils.managers import PassThroughManager
from model_utils.models import TimeStampedModel
from feder.cases.models import Case
from jsonfield import JSONField
from feder.questionaries.models import Questionary, Question
from feder.questionaries.modulator import modulators

_('Tasks index')


class TaskQuerySet(models.QuerySet):
    pass


class Task(TimeStampedModel):
    name = models.CharField(max_length=75, verbose_name=_("Name"))
    case = models.ForeignKey(Case, verbose_name=_("Case"))
    questionary = models.ForeignKey(Questionary, verbose_name=_("Questionary"),
        help_text=_("Questionary to fill by user as task"))
    objects = PassThroughManager.for_queryset_class(TaskQuerySet)()

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tasks:details', kwargs={'pk': self.pk})

    def lock_check(self):
        if self.questionary.lock is False:
            self.questionary.lock = True
            self.questionary.save()
            return True
        return False

    def save(self, lock_check=True, *args, **kwargs):
        if lock_check:
            self.lock_check()
        return super(Task, self).save(*args, **kwargs)

    class Meta:
        ordering = ['created', ]
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")


class SurveyQuerySet(models.QuerySet):
    def with_full_answer(self):
        return self.prefetch_related(models.Prefetch('answer_set',
                queryset=Answer.objects.select_related('question')))

    def with_user(self):
        return self.select_related('user')

    def for_task(self, task):
        return self.filter(task=task)


class Survey(TimeStampedModel):
    task = models.ForeignKey(Task)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    objects = PassThroughManager.for_queryset_class(SurveyQuerySet)()

    class Meta:
        ordering = ['created', ]
        verbose_name = _("Survey")
        verbose_name_plural = _("Surveys")
        unique_together = [('task', 'user')]


class Answer(models.Model):
    survey = models.ForeignKey(Survey)
    question = models.ForeignKey(Question)
    blob = JSONField()

    def render(self):
        return modulators[self.question.genre](self.question.blob).render_answer(self.blob)

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")
