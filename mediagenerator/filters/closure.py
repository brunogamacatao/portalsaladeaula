import tempfile

from django.conf import settings
from django.utils.encoding import smart_str
from mediagenerator.generators.bundles.base import Filter

COMPILATION_LEVEL = getattr(settings, 'CLOSURE_COMPILATION_LEVEL',
                            'SIMPLE_OPTIMIZATIONS')

class Closure(Filter):
    def __init__(self, **kwargs):
        self.config(kwargs, compilation_level=COMPILATION_LEVEL)
        super(Closure, self).__init__(**kwargs)
        assert self.filetype == 'js', (
            'Closure only supports compilation to js. '
            'The parent filter expects "%s".' % self.filetype)

    def get_output(self, variation):
        # We import this here, so App Engine Helper users don't get import
        # errors.
        from subprocess import Popen, PIPE
        for input in self.get_input(variation):
            # Creating a temporary file to store the compiler input
            print "Generating temporary file"
            temp = tempfile.NamedTemporaryFile()
            print "Done"
            print "Writing stuff to the file"
            temp.write(smart_str(input))
            temp.flush()
            print "Done"

            try:
                compressor = settings.CLOSURE_COMPILER_PATH
                cmd = Popen(['java', '-jar', compressor,
                             '--charset', 'utf-8',
                             '--js', temp.name,
                             '--compilation_level', self.compilation_level],
                            stdin=temp, stdout=PIPE, stderr=PIPE,
                            universal_newlines=True)
                print "Running the compressor"
                output, error = cmd.communicate()
                print "Done"
                assert cmd.wait() == 0, 'Command returned bad result:\n%s' % error
                temp.close() # Close, and remove, the temporary file
                yield output.decode('utf-8')
            except Exception, e:
                if temp:
                    temp.close() # Close, and remove, the temporary file
                raise ValueError("Failed to execute Java VM or Closure. "
                    "Please make sure that you have installed Java "
                    "and that it's in your PATH and that you've configured "
                    "CLOSURE_COMPILER_PATH in your settings correctly.\n"
                    "Error was: %s" % e)
