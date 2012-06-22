import logging
from django import template
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType

from portal.messages.models import Message
from django.utils.encoding import smart_unicode
from operator import attrgetter

register = template.Library()

class BaseMessageNode(template.Node):
    """
    Base helper class (abstract) for handling the get_message_* template tags.
    Looks a bit strange, but the subclasses below should make this a bit more
    obvious.
    """

    #@classmethod
    def handle_token(cls, parser, token):
        """Class method to parse get_message_list/count/form and return a Node."""
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
                ctype = BaseMessageNode.lookup_content_type(tokens[2], tokens[0]),
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

    def __init__(self, ctype=None, object_pk_expr=None, object_expr=None, as_varname=None, message=None):
        if ctype is None and object_expr is None:
            raise template.TemplateSyntaxError("Message nodes must be given either a literal object or a ctype and object pk.")
        self.message_model = Message
        self.as_varname = as_varname
        self.ctype = ctype
        self.object_pk_expr = object_pk_expr
        self.object_expr = object_expr
        self.message = message

    def render(self, context):
        qs = self.get_query_set(context)
        context[self.as_varname] = self.get_context_value_from_queryset(context, qs)
        return ''

    def get_query_set(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        if not object_pk:
            return self.message_model.objects.none()

        qs = self.message_model.objects.filter(
            content_type = ctype,
            object_pk    = smart_unicode(object_pk),
            is_reply     = False,
        )

        return qs

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

class MessageListNode(BaseMessageNode):
    """Insert a list of messages into the context."""
    def get_context_value_from_queryset(self, context, qs):
        return list(qs)

class MessageCountNode(BaseMessageNode):
    """Insert a count of messages into the context."""
    def get_context_value_from_queryset(self, context, qs):
        return qs.count()

class RenderMessageListNode(MessageListNode):
    """Render the message list directly"""

    #@classmethod
    def handle_token(cls, parser, token):
        """Class method to parse render_message_list and return a Node."""
        tokens = token.contents.split()
        if tokens[1] != 'for':
            raise template.TemplateSyntaxError("Second argument in %r tag must be 'for'" % tokens[0])

        # {% render_message_list for obj %}
        if len(tokens) == 3:
            return cls(object_expr=parser.compile_filter(tokens[2]))

        # {% render_message_list for app.models pk %}
        elif len(tokens) == 4:
            return cls(
                ctype = BaseMessageNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3])
            )
    handle_token = classmethod(handle_token)

    def render(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        if object_pk:
            obj = self.object_expr.resolve(context)

            if obj.messages_cache and obj.messages_cache != '':
                return obj.messages_cache
            else:
                template_search_list = [
                    "messages/%s/%s/list.html" % (ctype.app_label, ctype.model),
                    "messages/%s/list.html" % ctype.app_label,
                    "messages/list.html"
                ]

                qs = self.get_query_set(context)
                m_list = sorted(list(qs), key=attrgetter('earlier_date'), reverse=True)

                context.push()
                liststr = render_to_string(template_search_list, {
                    "message_list" : self.get_context_value_from_queryset(context, m_list),
                    "message_count": qs.count(),
                }, context)
                context.pop()

                obj.messages_cache = liststr
                obj.save()
            
                return liststr
        else:
            return ''

class ReplyCountNode(BaseMessageNode):
    #@classmethod
    def handle_token(cls, parser, token):
        """Class method to parse get_message_list/count/form and return a Node."""
        tokens = token.contents.split()
        if tokens[1] != 'as':
            raise template.TemplateSyntaxError("Second argument in %r tag must be 'as'" % tokens[0])

        # {% get_whatever for obj as varname %}
        if len(tokens) == 3:
            return cls(
                object_expr = parser.compile_filter('user'),
                as_varname  = tokens[2],
            )
        else:
            raise template.TemplateSyntaxError("%r tag requires 2 arguments" % tokens[0])

    handle_token = classmethod(handle_token)

    def get_query_set(self, context):
        obj = self.object_expr.resolve(context)
        return Message.objects.get_replies(user=obj)

    """Insert a count of messages into the context."""
    def get_context_value_from_queryset(self, context, qs):
        return len(qs)

class RenderReplyListNode(MessageListNode):
    """Render the reply list directly"""

    #@classmethod
    def handle_token(cls, parser, token):
        return cls(object_expr=parser.compile_filter("user"))
    handle_token = classmethod(handle_token)

    def render(self, context):
        obj = self.object_expr.resolve(context)
        ctype, object_pk = self.get_target_ctype_pk(context)
        template_search_list = ["messages/list.html"]

        messages = Message.objects.get_replies(user=obj)

        context.push()
        liststr = render_to_string(template_search_list, {
            "message_list" : self.get_context_value_from_queryset(context, messages),
            "message_count": len(messages),
        }, context)
        context.pop()
        return liststr


# We could just register each classmethod directly, but then we'd lose out on
# the automagic docstrings-into-admin-docs tricks. So each node gets a cute
# wrapper function that just exists to hold the docstring.

#@register.tag
def get_message_count(parser, token):
    """
    Gets the message count for the given params and populates the template
    context with a variable containing that value, whose name is defined by the
    'as' clause.

    Syntax::

        {% get_message_count for [object] as [varname]  %}
        {% get_message_count for [app].[model] [object_id] as [varname]  %}

    Example usage::

        {% get_message_count for event as message_count %}
        {% get_message_count for calendar.event event.id as message_count %}
        {% get_message_count for calendar.event 17 as message_count %}

    """
    return MessageCountNode.handle_token(parser, token)

#@register.tag
def get_message_list(parser, token):
    """
    Gets the list of messages for the given params and populates the template
    context with a variable containing that value, whose name is defined by the
    'as' clause.

    Syntax::

        {% get_message_list for [object] as [varname]  %}
        {% get_message_list for [app].[model] [object_id] as [varname]  %}

    Example usage::

        {% get_message_list for event as message_list %}
        {% for message in message_list %}
            ...
        {% endfor %}

    """
    return MessageListNode.handle_token(parser, token)

#@register.tag
def render_message_list(parser, token):
    """
    Render the message list (as returned by ``{% get_message_list %}``)
    through the ``messages/list.html`` template

    Syntax::

        {% render_message_list for [object] %}
        {% render_message_list for [app].[model] [object_id] %}

    Example usage::

        {% render_message_list for event %}

    """
    return RenderMessageListNode.handle_token(parser, token)

def get_reply_count(parser, token):
    return ReplyCountNode.handle_token(parser, token)


def render_reply_list(parser, token):
    return RenderReplyListNode.handle_token(parser, token)

register.tag(get_message_count)
register.tag(get_message_list)
register.tag(render_message_list)
register.tag(get_reply_count)
register.tag(render_reply_list)