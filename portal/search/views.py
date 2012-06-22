from django.http import HttpResponse
from django.views.generic.simple import direct_to_template

from portal.models import UserInfo, Institution, Course, Discipline
from portal.utils import split_string

def search(request):
    words = split_string(request.GET.get('q', ''))

    queryU = UserInfo.objects.all()
    queryI = Institution.objects.all()
    queryC = Course.objects.all()
    queryD = Discipline.objects.all()

    for word in words:
        queryU = queryU.filter(index=word)
        queryI = queryI.filter(index=word)
        queryC = queryC.filter(index=word)
        queryD = queryD.filter(index=word)

    result = []
    result += list(queryU)
    result += list(queryI)
    result += list(queryC)
    result += list(queryD)

    ctx = {
        'result': result,
    }

    return direct_to_template(request, 'search/list.html', ctx)