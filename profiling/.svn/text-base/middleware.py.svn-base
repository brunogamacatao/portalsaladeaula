import sys
import tempfile
import hotshot
import hotshot.stats
from django.conf import settings
from cStringIO import StringIO
from guppy import hpy

from models import ProfilerData

class ProfileMiddleware(object):
	"""
	Displays hotshot profiling for any view.
	http://yoursite.com/yourview/?prof

	Add the "prof" key to query string by appending ?prof (or &prof=)
	and you'll see the profiling results in your browser.
	It's set up to only be available in django's debug mode,
	but you really shouldn't add this middleware to any production configuration.
	* Only tested on Linux
	"""
	def process_request(self, request):
		if request.GET.has_key('prof'):
			self.tmpfile = tempfile.NamedTemporaryFile()
			self.prof = hotshot.Profile(self.tmpfile.name)

	def process_view(self, request, callback, callback_args, callback_kwargs):
		if request.GET.has_key('prof'):
			return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

	def process_response(self, request, response):   	
		if request.GET.has_key('prof'):
			h = hpy()
			mem_profile = h.heap()
			pd = ProfilerData(
				view = request.path,
				)
			
			self.prof.close()

			out = StringIO()
			old_stdout = sys.stdout
			sys.stdout = out

			stats = hotshot.stats.load(self.tmpfile.name)
			#stats.strip_dirs()
			stats.sort_stats('cumulative')
			stats.print_stats()

			sys.stdout = old_stdout
			stats_str = out.getvalue()

			if response and response.content and stats_str:
				response.content = "<h1>Instance wide RAM usage</h1><pre>%s</pre><br/><br/><br/><h1>CPU Time for this request</h1><pre>%s</pre>" % (
					mem_profile, stats_str
					)
				
			pd.profile = "Instance wide RAM usage\n\n%s\n\n\nCPU Time for this request\n\n%s" % (mem_profile, stats_str)
			pd.save()
		return response
