import os
import shutil
import logging

from organize.utils import Path, find_unused_filename

from .action import Action
from .trash import Trash


class Rename(Action):

    """
    Renames a file.

    :param str name:
        The new filename.
        Can be a format string which uses file attributes from a filter.

    :param bool overwrite:
        specifies whether existing files should be overwritten.
        Otherwise it will start enumerating files (append a counter to the
        filename) to resolve naming conflicts. [Default: False]

    Examples:
        - Convert all .PDF file extensions to lowercase (.pdf):

          .. code-block:: yaml

                # config.yaml
                rules:
                - folders: '~/Desktop'
                  filters:
                    - Extension: PDF
                  actions:
                    - Rename: "{path.stem}.pdf"
    """

    def __init__(self, name: str, overwrite=False):
        if os.path.sep in name:
            ValueError('Rename only takes a filename as argument. To move '
                       'files between folders use the Move action.')
        self.name = name
        self.overwrite = overwrite
        self.log = logging.getLogger(__name__)

    def run(self, basedir: Path, path: Path, attrs: dict, simulate: bool) -> Path:
        full_path = path.expanduser()
        expanded_name = self.fill_template_tags(self.name, basedir, full_path, attrs)
        new_path = full_path.parent / expanded_name

        # handle filename collisions
        if new_path.exists() and not new_path.samefile(full_path):
            if self.overwrite:
                self.print('Overwriting existing file!')
                Trash().run(basedir, path=new_path, attrs=attrs, simulate=simulate)
            else:
                new_path = find_unused_filename(new_path)

        self.print('New name: "%s"' % new_path.name)
        if not simulate:
            self.log.info('Renaming "%s" to "%s".', full_path, new_path)
            full_path.rename(new_path)
        return new_path

    def __str__(self):
        return 'Rename(name=%s, overwrite=%s)' % (self.name, self.overwrite)
