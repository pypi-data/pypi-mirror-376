from cement import App, TestApp, init_defaults
from cement.core import foundation, hook
from cement.utils import shell
from cement.utils.version import get_version_banner

from .core.version import get_version
from .controllers.base import Base

VERSION_BANNER = """
ML & data helper code! %s
%s
""" % (get_version(), get_version_banner())

class DataToolkit(App):
    """Data Toolkit primary application."""

    class Meta:
        label = 'dt'

        # configuration defaults
        config_defaults = init_defaults('dt')

        # call sys.exit() on close
        exit_on_close = True

        # load additional framework extensions
        extensions = [
            'yaml',
            'colorlog',
            'jinja2',
        ]

        # configuration handler
        config_handler = 'yaml'

        # configuration file suffix
        config_file_suffix = '.yml'

        # set the log handler
        log_handler = 'colorlog'

        # set the output handler
        output_handler = 'jinja2'

        # register handlers
        handlers = [
            Base
        ]

        # register hooks
        hooks = []

        # register templates
        template_module = 'dt.templates'

        # The file extension for templates
        template_dirs = []

        # The default template engine to use
        template_handler = 'jinja2'

def main():
    with DataToolkit() as app:
        app.run()

if __name__ == '__main__':
    main()
