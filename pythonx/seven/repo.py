#! /usr/bin/env python3

import os.path as p
import pprint as pp
import re

import svn.local

def trim_leading_lines(txt, num_newlines):
    assert num_newlines > 0
    index = 0
    for i in range(num_newlines):
        index = txt.find('\n', index + 1)
    return txt[index + 1:]



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
        self._root_dir = p.abspath(p.expanduser(root_dir))
        self._client = svn.local.LocalClient(self._root_dir)

    def _to_svnroot_relative_path(self, filepath):
        f = p.expanduser(filepath)
        # For some reason, relpath still makes me relative to cwd insted of to
        # the input path. Use relpace instead (expanduser gives us absolute
        # path).
        # XX f = p.relpath(f, self._root_dir)
        f = f.replace(self._root_dir + '/', '')
        return f

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

        def fmt(status):
            # Print in this style:
            # M pythonx/seven.py
            return '{} {}'.format(self.status_map[status.type], self._to_svnroot_relative_path(status.name))

        headers = [
            '\nStaged ({count})',
            '\nUnstaged ({count})',
            '\nUntracked ({count})',
        ]
        staged, unstaged, untracked = self._get_stage_status_text(fmt, headers)
        return """Head: {} 
{}{}{}
""".format(self.get_branch(), staged, unstaged, untracked)

    def request_stage(self, filepath):
        """Stage the input file.
    
        request_stage(str) -> None
        """
        self._client.add(filepath)
        # TODO: locally store it as staged and modify _status_text. Only actually stage it when we commit.

    def _get_stage_status(self):
        """Get the status repo's staged files.
    
        _get_stage_status() -> list(str), list(str), list(str)
        """
        staged    = []
        unstaged  = []
        untracked = []
        staged_types = [
            svn.constants.ST_ADDED,
            svn.constants.ST_DELETED,
            svn.constants.ST_MODIFIED,
            svn.constants.ST_REPLACED,
        ]
        for status in self._client.status():
            if status.type in staged_types:
                staged.append(status)
            elif status.type == svn.constants.ST_UNVERSIONED:
                untracked.append(status)
            else:
                unstaged.append(status)

        return staged, unstaged, untracked


    def _get_stage_status_text(self, fmt, headers):
        """Get the status repo's staged files.
    
        _get_stage_status_text() -> str, str, str
        """
        staged, unstaged, untracked = self._get_stage_status()
        staged, unstaged, untracked = [
            [headers[i].format(count=len(c))]
            + [fmt(status)
               for status in c]
            for i,c in enumerate([staged, unstaged, untracked])]

        def _join_if_has_files(files):
            if len(files) > 1:
                return "\n".join(files) + "\n"
            return ""
        staged, unstaged, untracked = [_join_if_has_files(x) for x in [staged, unstaged, untracked]]
        return staged, unstaged, untracked


    def _commit_text(self):
        def fmt(status):
            # Print in this style:
            #	new file:   pythonx/seven.py
            return '#\t{}:\t{}'.format(status.type_raw_name, self._to_svnroot_relative_path(status.name))

        headers = [
            '#\n# Changes to be committed:',
            '#\n# Changes not staged for commit:',
            '#\n# Untracked files:',
        ]
        staged, unstaged, untracked = self._get_stage_status_text(fmt, headers)
        diff = self._unified_diff(self._root_dir, 'HEAD', '')
        txt = '''
# Please enter the commit message for your changes. Lines starting
# with '#' will be ignored, and an empty message aborts the commit.
#
# On branch {branch}
{staged}{unstaged}{untracked}#
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
        # self._client.diff('hello', 'HEAD', '')
        # self._client.diff() doesn't work since it tries to give us the diff
        # in a list and I don't wnat ot put it back together again.
        d = self._client.run_command(
            'diff',
            ['--git',
             '--old', '{0}@{1}'.format(full_url_or_path, old),
             '--new', '{0}@{1}'.format(full_url_or_path, new),
             ],
            do_combine=True)
        d = d.decode('utf8')
        return d

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

    def cat_file(self, filepath, revision):
        f = self._client.cat(self._to_svnroot_relative_path(filepath), revision)
        # Why doesn't svn produce utf output?
        f = f.decode('utf8')
        # Remove incorrect trailing space
        return f[:-1]

    def get_buffer_name_for_file(self, filepath, revision):
        filepath = self._to_svnroot_relative_path(p.expanduser(filepath))
        print('get_buffer_name_for_file', filepath)
        i = self._client.info(filepath, revision)
        name = i['url']
        colon = name.find(':')
        assert colon > 0, "Expected url always includes a protocol"
        return 'seven' + name[colon:]


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
    print()
    print('Scommit')
    print(r._commit_text())
    print()
    print('Sdiff')
    print(r.cat_file('subdir/hastrailingnewline', 'HEAD'))

    print()
    print('done')



if __name__ == "__main__":
    test()
