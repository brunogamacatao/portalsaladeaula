import cProfile, pstats
import StringIO

class ProfileMiddleware(object):
    def process_request(self, request):
        if request.GET.has_key('prof'):
            self.prof = cProfile.Profile()

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if request.GET.has_key('prof'):
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def process_response(self, request, response):
        if request.GET.has_key('prof'):
            stream = StringIO.StringIO()
            stats = pstats.Stats(self.prof, stream=stream)
            stats.sort_stats("time")
            stats.print_stats(80)
            response.content += '<!-- %s -->' % stream.getvalue()
        
        return response
