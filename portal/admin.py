from django.contrib import admin
from portal.models import *
from portal.polls.models import *

admin.site.register(UserInfo)
admin.site.register(Institution)
admin.site.register(Course)
admin.site.register(Discipline)
admin.site.register(UserInstitutionRole)
admin.site.register(UserCourseRole)
admin.site.register(UserDisciplineRole)
admin.site.register(Poll)
admin.site.register(Group)
admin.site.register(Question)
admin.site.register(Answer)