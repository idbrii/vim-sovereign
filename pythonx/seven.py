#! /usr/bin/env python

import os.path as p
import pprint as pp
import re

import svn.local

class SvnError(Exception):

    """Docstring for SvnError. """

    def __init__(self, msg):
        """

        :msg: TODO

        """
        Exception.__init__(self, msg)
        

class Repo(object):
    """Docstring for Repo. """

    # http://svn.apache.org/viewvc/subversion/trunk/subversion/svn/schema/status.rnc?view=markup
    # Re-using symbols from `git status --porcelain=v2` to look like
    # fugitive or svn st. Using full words for ones I don't understand and
    # haven't seen.
    status_map = [
        "",
        "A", # ST_ADDED       = 1
        "c", # ST_CONFLICTED  = 2
        "?", # ST_DELETED     = 3
        "x", # ST_EXTERNAL    = 4
        "!", # ST_IGNORED     = 5
        "incomplete", # ST_INCOMPLETE  = 6
        "merged", # ST_MERGED      = 7
        "?", # ST_MISSING     = 8
        "M", # ST_MODIFIED    = 9
        "none", # ST_NONE        = 10
        "normal", # ST_NORMAL      = 11
        "obstructed", # ST_OBSTRUCTED  = 12
        "replaced", # ST_REPLACED    = 13
        "?", # ST_UNVERSIONED = 14
    ]

    def __init__(self, root_dir):
        """ Create a repo object that helps interface with the svn
        repository. A wrapper around svn.local.LocalClient.

        :root_dir: The root directory for the svn repo.

        """
        self._root_dir = p.expanduser(root_dir)
        self._client = svn.local.LocalClient(self._root_dir)

    def _to_svnroot_relative_path(self, absolute_path):
        return p.relpath(absolute_path, self._root_dir)

    def get_branch(self):
        i = self._client.info()
        url = i['url']
        if 'branches' in url:
            url = re.sub('.*/branches/', '', url, 1, '')
            return p.dirname(url)
        elif '/trunk/' in url:
            return 'trunk'
        else:
            return '?'

    def _status_text(self, optional_path=None):
        """Get buffer text contents for Sstatus

        _status_text(svn.local.LocalClient, str) -> str
        """

        # Head: master
        # 
        # Untracked (2)
        # ? autoload/
        # ? plugin/
        # 
        # Unstaged (1)
        # M pythonx/seven.py
        # 
        # Staged (1)
        # A pythonx/seven.py
        s = self._client.status(optional_path)
        lines = ['{} {}'.format(self.status_map[status.type], self._to_svnroot_relative_path(status.name)) for status in s]
        return "\n".join(lines)

    def request_stage(self, filepath):
        """Stage the input file.
    
        request_stage(str) -> None
        """
        self._client.add(filepath)
        # TODO: locally store it as staged and modify _status_text. Only actually stage it when we commit.

    def _get_stage_status(self):
        """Get the status repo's staged files.
    
        _get_stage_status() -> str, str, str
        """
        def fmt(name, svn_type_str):
            #	new file:   pythonx/seven.py
            return '#\t{}:\t{}'.format(svn_type_str, self._to_svnroot_relative_path(name))
        staged    = ['#\n# Changes to be committed:\n'      ]
        unstaged  = ['#\n#\n# Changes not staged for commit:\n']
        untracked = ['#\n#\n# Untracked files:\n'              ]
        staged_types = [
            svn.constants.ST_ADDED,
            svn.constants.ST_DELETED,
            svn.constants.ST_MODIFIED,
            svn.constants.ST_REPLACED,
        ]
        for status in self._client.status():
            txt = fmt(status.name, status.type_raw_name)
            if status.type in staged_types:
                staged.append(txt)
            elif status.type == svn.constants.ST_UNVERSIONED:
                untracked.append(txt)
            else:
                unstaged.append(txt)

        def _join_if_has_files(files):
            if len(files) > 1:
                return "".join(files)
            return ""
        staged, unstaged, untracked = [_join_if_has_files(x) for x in [staged, unstaged, untracked]]
        return staged, unstaged, untracked


    def _commit_text(self):
        staged, unstaged, untracked = self._get_stage_status()
        diff = self._unified_diff(self._root_dir, 'HEAD', '')
        txt = '''
# Please enter the commit message for your changes. Lines starting
# with '#' will be ignored, and an empty message aborts the commit.
#
# On branch {branch}
{staged}{unstaged}{untracked}
#
# ------------------------ >8 ------------------------
# Do not modify or remove the line above.
# Everything below it will be ignored.
{diff}'''.format(
    branch=self.get_branch(),
    staged=staged,
    unstaged=unstaged,
    untracked=untracked,
    diff=diff,
)
        return txt

    def _unified_diff(self, full_url_or_path, old, new):
        # self._client.diff() doesn't work since it tries to give us the diff
        # in a list and I don't wnat ot put it back together again.
        d = self._client.run_command(
            'diff',
            ['--git',
             '--old', '{0}@{1}'.format(full_url_or_path, old),
             '--new', '{0}@{1}'.format(full_url_or_path, new),
             ],
            do_combine=True)
        return d.decode('utf8')

    def commit(self):
        """Commit current changes
    
        commit() -> None
        """
        self._client.commit(message, rel_filepaths)

    def update(self, single_file=None, revision=None):
        """Get latest revision from server
    
        update() -> None
        """
        if not single_file:
            single_file = [single_file]
        else:
            single_file = []
        self._client.update(rel_filepaths, single_file, revision)


def get_repo(working_copy_file):
    root = _find_svnroot_for_file(p.expanduser(working_copy_file))
    return Repo(root)


def _find_svnroot_for_file(working_copy_file):
    """Find svn root dir for the working_copy_file

    Finds the first directory in ancestors that contains a .svn folder.

    find_client(str) -> str
    """
    prev_dir = None
    directory = p.abspath(working_copy_file)
    while directory != prev_dir:
        prev_dir = directory
        directory = p.dirname(prev_dir)
        svn_dir = p.join(directory, '.svn')
        if p.isdir(svn_dir):
            return directory
        else:
            print("is not svndir: {}".format(svn_dir))

    raise SvnError("Could not find repo for {}".format(working_copy_file))


def create_status_buffer(working_copy_file):
    """Create a Sstatus buffer.

    create_status_buffer(str) -> None
    """
    pass

def test():
    import os
    os.chdir(p.expanduser('~/data/code/svntest/checkout/'))
    r = get_repo('~/data/code/svntest/checkout/hello')

    print()
    print('Sstatus')
    print(r._status_text())
    print()
    print('seven#branch()')
    print(r.get_branch())
    # pp.pprint(r._client.info())
    print()
    print('Scommit')
    print(r._commit_text())

test()
