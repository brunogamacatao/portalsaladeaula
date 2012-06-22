from django import template
from django.template import NodeList
from functools import wraps
import inspect, logging, sys
from portal.models import Institution, Course, Discipline, RelUserInstitution, UserInstitutionRole, RelUserCourse, UserCourseRole, RelUserDiscipline, UserDisciplineRole

def condition_tag(func):
    """ Generic conditional templatetag decorator.

    Example - how to define a conditional tag:
        @register.tag
        @condition_tag
        def if_can_foo(object, user='user'):
            return user.can_foo(object)

    Example - how to use it in the template:
        {% if_can_foo object user %}
        ...
        {% else %}
        ...
        {% endif_can_foo %}

    Or - we can leave out the second parameter, and it will default
    to 'user':
        {% if_can_foo object %}
        ...

    In python, the if_can_foo function's arguments are the expected
    arguments to the template tag. In this case, the first argument
    should be the object, the second argument should be the user. The
    return value must be either True or False, corresponding to the
    if/else sections of the condition node in the template.

    Default arguments for the function (e.g. user='user') will be
    processed by the context that the template tag resides in. In this
    case, it will resolve the global 'user' name, and in the function,
    we will be accessing the resultant object. If this value does not
    exist in the template's context, it will break.
    """

    class ConditionNode(template.Node):
        def __init__(self, arg_expressions, nodelist_true, nodelist_false):
            self.arg_expressions = arg_expressions
            self.nodelist_true   = nodelist_true
            self.nodelist_false  = nodelist_false

        def render(self, context):
            params = [ i.resolve(context) for i in self.arg_expressions ]
            if func(*params):
                return self.nodelist_true.render(context)
            else:
                return self.nodelist_false.render(context)

    @wraps(func)
    def wrapper(parser, token):
        bits = token.contents.split()

        # Get the parameters and default parameters for the decorated function
        argspec = inspect.getargspec(func)
        params = argspec[0]
        defaults = list(argspec[3])
        if defaults:
            default_params = dict(zip([i for i in reversed(params)],
                                      [i for i in reversed(defaults)] ))
        else:
            default_params = {}

        # Try to display nice template errors
        if len(bits) > len(params)+1 or len(bits) <= len(params)-len(defaults):
            error = (
                '"%s" accepts %d arguments: %s' %
                (bits[0], len(params), ', '.join(params),)
            )
            raise template.TemplateSyntaxError, error

        # Get the (string) arguments from the template
        arg_expressions = []
        for i in range(len(params)):
            try:
                # Try to use the parameter given by the template
                arg_expressions.append(parser.compile_filter(bits[i+1]))
            except IndexError:
                # If it doesn't exist, use the default value
                arg_expressions.append(
                    parser.compile_filter(default_params[params[i]])
                )

        # Parse out the true and false nodes
        nodelist_true = parser.parse(('else', 'end'+bits[0],))
        token = parser.next_token()
        if token.contents == 'else':
            nodelist_false = parser.parse(('end'+bits[0],))
            parser.delete_first_token()
        else:
            nodelist_false = NodeList()
        return ConditionNode(arg_expressions, nodelist_true, nodelist_false)
    return wrapper

register = template.Library()

@register.tag
@condition_tag
def if_is_owner(object, user='user'):
    """ A function that determines if the logged user owns an institution,
    course or discipline.
    """
    logging.info('if_is_owner(%s, %s)' % (str(type(object)), user.username))
    try:
        if user.is_superuser:
            logging.info('is superuser !')
            return True
        if isinstance(object, Institution):
            logging.info('an Institution')
            if user.get_profile().owner_set.filter(institution=object).exists():
                return True
            if user.get_profile().is_teacher and RelUserInstitution.objects.filter(institution=object,user=user.get_profile(),role=UserInstitutionRole.objects.teacher_role()).exists():
                return True
        elif isinstance(object, Course):
            logging.info('a Course')
            if user.get_profile().course_owner_set.filter(course=object).exists():
                return True
            if user.get_profile().is_teacher and RelUserCourse.objects.filter(course=object,user=user.get_profile(),role=UserCourseRole.objects.teacher_role()).exists():
                return True
        elif isinstance(object, Discipline):
            logging.info('a Discipline')
            if user.get_profile().discipline_owner_set.filter(discipline=object).exists():
                return True
            if user.get_profile().is_teacher and RelUserDiscipline.objects.filter(discipline=object,user=user.get_profile(),role=UserDisciplineRole.objects.teacher_role()).exists():
                return True
        return False
    except:
        logging.error('Exception: %s' % (sys.exc_info()[0],))
        return False

@register.tag
@condition_tag
def if_is_a_member(object, user='user'):
    """ A function that determines if the logged user is a member of an
    institution, course or discipline.
    """
    logging.info('if_is_member(%s, %s)' % (str(type(object)), user.username))
    try:
        if user.is_superuser:
            logging.info('is superuser !')
            return True
        if isinstance(object, Institution):
            logging.info('an Institution')
            if RelUserInstitution.objects.filter(institution=object,user=user.get_profile()).exists():
                return True
        elif isinstance(object, Course):
            logging.info('a Course')
            if RelUserCourse.objects.filter(course=object,user=user.get_profile()).exists():
                return True
        elif isinstance(object, Discipline):
            logging.info('a Discipline')
            if RelUserDiscipline.objects.filter(discipline=object,user=user.get_profile()).exists():
                return True
        return False
    except:
        logging.error('Exception: %s' % (sys.exc_info()[0],))
        return False

@register.tag
@condition_tag
def if_is_facisa(user='user'):
    facisa = Institution.objects.get(slug='facisa')
    return RelUserInstitution.objects.filter(institution=facisa,user=user.get_profile()).exists()