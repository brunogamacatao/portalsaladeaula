from django import template
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType

from portal.updates.models import Update

register = template.Library()

class BaseUpdateNode(template.Node):
    """
    Base helper class (abstract) for handling the get_update_* template tags.
    Looks a bit strange, but the subclasses below should make this a bit more
    obvious.
    """

    #@classmethod
    def handle_token(cls, parser, token):
        """Class method to parse get_update_list/count/form and return a Node."""
        tokens = token.contents.split()
        if tokens[1] != 'for':
            raise template.TemplateSyntaxError("Second argument in %r tag must be 'for'" % tokens[0])

        # {% get_whatever for obj as varname %}
        if len(tokens) == 5:
            if tokens[3] != 'as':
                raise template.TemplateSyntaxError("Third argument in %r must be 'as'" % tokens[0])
            return cls(
                object_expr = parser.compile_filter(tokens[2]),
                as_varname = tokens[4],
            )

        # {% get_whatever for app.model pk as varname %}
        elif len(tokens) == 6:
            if tokens[4] != 'as':
                raise template.TemplateSyntaxError("Fourth argument in %r must be 'as'" % tokens[0])
            return cls(
                ctype = BaseUpdateNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3]),
                as_varname = tokens[5]
            )

        else:
            raise template.TemplateSyntaxError("%r tag requires 4 or 5 arguments" % tokens[0])

    handle_token = classmethod(handle_token)

    #@staticmethod
    def lookup_content_type(token, tagname):
        try:
            app, model = token.split('.')
            return ContentType.objects.get(app_label=app, model=model)
        except ValueError:
            raise template.TemplateSyntaxError("Third argument in %r must be in the format 'app.model'" % tagname)
        except ContentType.DoesNotExist:
            raise template.TemplateSyntaxError("%r tag has non-existant content-type: '%s.%s'" % (tagname, app, model))
    lookup_content_type = staticmethod(lookup_content_type)

    def __init__(self, ctype=None, object_pk_expr=None, object_expr=None, as_varname=None, update=None):
        if ctype is None and object_expr is None:
            raise template.TemplateSyntaxError("Update nodes must be given either a literal object or a ctype and object pk.")
        self.update_model = Update
        self.as_varname = as_varname
        self.ctype = ctype
        self.object_pk_expr = object_pk_expr
        self.object_expr = object_expr
        self.update = update

    def render(self, context):
        qs = self.get_query_set(context)
        context[self.as_varname] = self.get_context_value_from_queryset(context, qs)
        return ''

    def get_query_set(self, context):
        obj = self.object_expr.resolve(context)
        return obj.get_update_list()
#        ctype, object_pk = self.get_target_ctype_pk(context)
#        if not object_pk:
#            return self.update_model.objects.none()
#
#        qs = self.update_model.objects.filter(
#            content_type = ctype,
#            object_pk    = smart_unicode(object_pk),
#        )
#
#        return qs

    def get_target_ctype_pk(self, context):
        if self.object_expr:
            try:
                obj = self.object_expr.resolve(context)
            except template.VariableDoesNotExist:
                return None, None
            return ContentType.objects.get_for_model(obj), obj.pk
        else:
            return self.ctype, self.object_pk_expr.resolve(context, ignore_failures=True)

    def get_context_value_from_queryset(self, context, qs):
        """Subclasses should override this."""
        raise NotImplementedError

class UpdateListNode(BaseUpdateNode):
    """Insert a list of updates into the context."""
    def get_context_value_from_queryset(self, context, qs):
        return list(qs)

class UpdateCountNode(BaseUpdateNode):
    """Insert a count of updates into the context."""
    def get_context_value_from_queryset(self, context, qs):
        return len(qs)

class RenderUpdateListNode(UpdateListNode):
    """Render the update list directly"""

    #@classmethod
    def handle_token(cls, parser, token):
        """Class method to parse render_update_list and return a Node."""
        tokens = token.contents.split()
        if tokens[1] != 'for':
            raise template.TemplateSyntaxError("Second argument in %r tag must be 'for'" % tokens[0])

        # {% render_update_list for obj %}
        if len(tokens) == 3:
            return cls(object_expr=parser.compile_filter(tokens[2]))

        # {% render_update_list for app.models pk %}
        elif len(tokens) == 4:
            return cls(
                ctype = BaseUpdateNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3])
            )
    handle_token = classmethod(handle_token)

    def render(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        if object_pk:
            obj = self.object_expr.resolve(context)
            if obj.updates_cache:
                return obj.updates_cache
            else:
                template_search_list = [
                    "updates/%s/%s/list.html" % (ctype.app_label, ctype.model),
                    "updates/%s/list.html" % ctype.app_label,
                    "updates/list.html"
                ]
                qs = self.get_query_set(context)
                context.push()
                liststr = render_to_string(template_search_list, {
                    "update_list" : self.get_context_value_from_queryset(context, qs)
                }, context)
                context.pop()

                obj.updates_cache = liststr
                obj.save()
            
                return liststr
        else:
            return ''

# We could just register each classmethod directly, but then we'd lose out on
# the automagic docstrings-into-admin-docs tricks. So each node gets a cute
# wrapper function that just exists to hold the docstring.

#@register.tag
def get_update_count(parser, token):
    """
    Gets the update count for the given params and populates the template
    context with a variable containing that value, whose name is defined by the
    'as' clause.

    Syntax::

        {% get_update_count for [object] as [varname]  %}
        {% get_update_count for [app].[model] [object_id] as [varname]  %}

    Example usage::

        {% get_update_count for event as update_count %}
        {% get_update_count for calendar.event event.id as update_count %}
        {% get_update_count for calendar.event 17 as update_count %}

    """
    return UpdateCountNode.handle_token(parser, token)

#@register.tag
def get_update_list(parser, token):
    """
    Gets the list of updates for the given params and populates the template
    context with a variable containing that value, whose name is defined by the
    'as' clause.

    Syntax::

        {% get_update_list for [object] as [varname]  %}
        {% get_update_list for [app].[model] [object_id] as [varname]  %}

    Example usage::

        {% get_update_list for event as update_list %}
        {% for update in update_list %}
            ...
        {% endfor %}

    """
    return UpdateListNode.handle_token(parser, token)

#@register.tag
def render_update_list(parser, token):
    """
    Render the update list (as returned by ``{% get_update_list %}``)
    through the ``updates/list.html`` template

    Syntax::

        {% render_update_list for [object] %}
        {% render_update_list for [app].[model] [object_id] %}

    Example usage::

        {% render_update_list for event %}

    """
    return RenderUpdateListNode.handle_token(parser, token)

register.tag(get_update_count)
register.tag(get_update_list)
register.tag(render_update_list)