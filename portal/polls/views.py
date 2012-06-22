# -*- coding: utf-8 -*-
import csv
import traceback
import logging

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.forms.formsets import formset_factory

from .models import Poll, Question, Answer, Choice, Group
from .forms import PollForm, QuestionForm, ChoiceForm, AnswerForm, GroupForm

from django.template import Context
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives

from portal.models import UserInfo, UserInstitutionRole, RelUserInstitution

def index(request):
    return HttpResponse('Funciona !')

@csrf_protect
@login_required
def poll_save(request, id=None):
    '''This function is used to create and edit polls.'''
    form = None
    ctx  = dict()

    if request.method == 'GET':
        if id:
            poll = get_object_or_404(Poll, pk=id)
            form = PollForm(instance=poll)
        else:
            form = PollForm()
    else:
        if id:
            poll = get_object_or_404(Poll, pk=id)
            form = PollForm(request.POST, instance=poll)
        else:
            form = PollForm(request.POST)

        if form.is_valid():
            poll = form.save(commit=True)

            return HttpResponseRedirect(reverse('portal.polls.views.poll_detail', args=[poll.pk,]))

    ctx['form'] = form

    return direct_to_template(request, 'polls/poll_form.html', ctx)

def poll_detail(request, id=None):
    '''This function is used to show the details of a poll.'''
    return HttpResponse("Funcionou !")

@csrf_protect
@login_required
def question_save(request, id=None):
    '''This function is used to create and edit questions associated to a poll.'''
    form = None
    ctx  = dict()

    if request.method == 'GET':
        if id:
            question = get_object_or_404(Question, pk=id)
            form     = QuestionForm(instance=question)
        else:
            form = QuestionForm()
    else:
        if id:
            question = get_object_or_404(Poll, pk=id)
            form     = QuestionForm(request.POST, instance=question)
        else:
            form = QuestionForm(request.POST)

        if form.is_valid():
            question = form.save(commit=True)

            return HttpResponseRedirect(reverse('portal.polls.views.question_save'))

    ctx['form'] = form

    return direct_to_template(request, 'polls/question_form.html', ctx)

@csrf_protect
@login_required
def choice_save(request, id=None):
    '''This function is used to create and edit questions' choices associated to a poll.'''
    form = None
    ctx  = dict()

    if request.method == 'GET':
        if id:
            choice = get_object_or_404(Choice, pk=id)
            form     = ChoiceForm(instance=choice)
        else:
            form = ChoiceForm()
    else:
        if id:
            choice = get_object_or_404(Choice, pk=id)
            form   = ChoiceForm(request.POST, instance=choice)
        else:
            form = ChoiceForm(request.POST)

        if form.is_valid():
            choice = form.save(commit=True)

            return HttpResponseRedirect(reverse('portal.polls.views.choice_save'))

    ctx['form'] = form

    return direct_to_template(request, 'polls/choice_form.html', ctx)

@csrf_protect
@login_required
def group_save(request, id=None):
    '''This function is used to create and edit groups of questions associated to a poll.'''
    form = None
    ctx  = dict()

    if request.method == 'GET':
        if id:
            group = get_object_or_404(Group, pk=id)
            form  = GroupForm(instance=group)
        else:
            form = GroupForm()
    else:
        if id:
            group  = get_object_or_404(Group, pk=id)
            form   = GroupForm(request.POST, instance=group)
        else:
            form = GroupForm(request.POST)

        if form.is_valid():
            group = form.save(commit=True)

            return HttpResponseRedirect(reverse('portal.polls.views.group_save'))

    ctx['form'] = form

    return direct_to_template(request, 'polls/group_form.html', ctx)


def answer(request, id):
    '''This function is called by users in order to answer a poll.'''
    if request.method == 'GET':
        poll = get_object_or_404(Poll, pk=id)

        question_count = 0
        for group in poll.group_set.all():
            question_count += group.question_set.count()

        class Counter:
            def __init__(self):
                self.value = -1

            def next(self):
                self.value += 1
                return self.value

            def value(self):
                return self.value

        ctx = dict()
        ctx['poll']           = poll
        ctx['question_count'] = question_count
        ctx['counter']        = Counter()


        return direct_to_template(request, 'polls/answer.html', ctx)
    else:
        AnswerFormSet = formset_factory(AnswerForm)
        formset = AnswerFormSet(request.POST, request.FILES)
        
        if formset.is_valid():
            for form in formset.forms:
                Answer(answer=form.cleaned_data['answer'],
                       question=form.cleaned_data['question']).save()

        return direct_to_template(request, 'polls/finish.html')

def send_mail(request, id):
    poll         = get_object_or_404(Poll, pk=id)
    student_role = UserInstitutionRole.objects.student_role()
    counter      = 0

    ctx = {
        'link': 'http://www.portalsaladeaula.com/polls/answer/%s' % str(poll.id),
    }

    subject      = "Por favor, responda a nossa pesquisa"
    from_email   = 'Portal Sala de Aula <gerencia@portalsaladeaula.com>'
    text_content = get_template('polls/email.txt').render(Context(ctx))
    html_content = get_template('polls/email.html').render(Context(ctx))

    for rel in RelUserInstitution.objects.filter(role=student_role).all():
        try :
            msg = EmailMultiAlternatives(subject, text_content, from_email, [rel.user.email, ])
            msg.attach_alternative(html_content, "text/html")

            try:
                msg.send()
                counter += 1
            except:
                logging.error('Não foi possível enviar o email')
                traceback.print_exc()
        except:
            pass

    return HttpResponse("%d emails enviados com sucesso" % counter)

def report(request, id):
    poll      = get_object_or_404(Poll, pk=id)
    maps      = dict()
    questions = []
    nrows     = 0

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=poll_report.csv'
    
    writer = csv.writer(response)

    for group in poll.group_set.all():
        for question in group.question_set.all():
            questions.append(question)
            maps[question.id] = question.answer_set.all()
            nrows = len(maps[question.id])

    writer.writerow(['%d.%d' % (q.group.sequence, q.sequence, ) for q in questions])

    for i in range(nrows):
        row = []
        for q in questions:
            if q.kind == 'M': #Multiple choice
                row.append(Choice.objects.get(pk=int(maps[q.id][i].answer)).choice.encode('ascii', 'ignore'))
            else:
                row.append(maps[q.id][i].answer)
        writer.writerow(row)

    return response