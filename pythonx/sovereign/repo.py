#! /usr/bin/env python3

from email.utils import format_datetime
import itertools
import os
import os.path as p
import pprint as pp
import re

try:
    import svn.local
    import svn.exception
except ImportError:
    print('pysvn not installed. Please run pip install -r ~/.vim/bundle/sovereign/requirements.txt')
    raise

_SNIP_MARKER = "------------------------ >8 ------------------------"

_root_to_repo = {}

def get_repo(working_copy_file):
    root = _find_svnroot_for_file(p.expanduser(working_copy_file))
    try:
        return _root_to_repo[root]
    except KeyError:
        r = Repo(root)
        _root_to_repo[root] = r
        return r

def trim_leading_lines(txt, num_newlines):
    assert num_newlines > 0
    index = 0
    for i in range(num_newlines):
        index = txt.find('\n', index + 1)
    return txt[index + 1:]

def _take_first_x_lines(txt, num_newlines):
    assert num_newlines > 0
    lines = txt.split('\n')
    return "\n".join(lines[:num_newlines])

def _prefix_lines(txt, prefix):
    lines = txt.split('\n')
    lines = [prefix + line for line in lines]
    return "\n".join(lines)



class SvnError(Exception):

    """Docstring for SvnError. """

    def __init__(self, msg):
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
        "C", # ST_CONFLICTED  = 2
        "D", # ST_DELETED     = 3
        "x", # ST_EXTERNAL    = 4
        "!", # ST_IGNORED     = 5
        "incomplete", # ST_INCOMPLETE  = 6
        "merged", # ST_MERGED      = 7
        "d", # ST_MISSING     = 8
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
        self._root_dir = p.realpath(p.abspath(p.expanduser(root_dir)))
        self._client = svn.local.LocalClient(self._root_dir)
        self._staged_files = []

    def _to_svnroot_relative_path(self, filepath):
        """Convert to relative paths. For display purposes only. We should
        store paths as absolute.
    
        _to_svnroot_relative_path(str) -> str
        """
        f = p.realpath(p.abspath(p.expanduser(filepath)))
        # For some reason, relpath sometimes gives results relative to
        # cwd insted of to the input path. Use replace instead.
        # (So far the only repro I've found is with symbolic links, but I think that's fixed.)
        f = p.relpath(f, self._root_dir)
        assert f == f.replace(self._root_dir + p.sep, ''), "relpath returned a different result than replace"
        return f

    def relative_to_absolute(self, rel_filepath):
        return p.join(self._root_dir, rel_filepath)

    def get_branch(self):
        i = self._client.info()
        url = i['url']
        if 'branches' in url:
            url = re.sub('.*/branches/', '', url, 1)
            return p.dirname(url)
        elif url.endswith('/trunk') or '/trunk/' in url:
            return 'trunk'
        else:
            return '?'

    def _status_text(self, optional_path=None):
        """Get buffer text contents for Sstatus

        _status_text(svn.local.LocalClient, str) -> str
        """
        # TODO: Support status for a directory since svn can be slow retrieving results from server.

        # Head: master
        # 
        # Untracked (2)
        # ? autoload/
        # ? plugin/
        # 
        # Unstaged (1)
        # M pythonx/sovereign.py
        # 
        # Staged (1)
        # A pythonx/sovereign.py
        #
        # Changelist[hello] (1)
        # M pythonx/vimapi.py

        def fmt(status):
            # Print in this style:
            # M pythonx/sovereign.py
            return '{} {}'.format(self.status_map[status.type], self._to_svnroot_relative_path(status.name))

        headers = [
            '\nStaged ({count})',
            '\nUnstaged ({count})',
            '\nUntracked ({count})',
            # changelist must be last
            '\nChangelist[{title}] ({count})',
        ]
        staged, unstaged, listed, untracked = self._get_stage_status_text(fmt, headers)
        return f"""Head: {self.get_branch()} 
{untracked}{unstaged}{staged}
{listed}
"""

    def request_stage_toggle(self, filepath):
        """Toggle whether input file is staged.

        Requires absolute filepaths.
        """
        assert p.isabs(filepath)
        if filepath in self._staged_files:
            self.request_unstage(filepath)
        else:
            self.request_stage(filepath)

    def request_stage(self, filepath):
        """Stage the input file.
    
        request_stage(str) -> None
        """
        assert p.isabs(filepath)
        rel_path = self._to_svnroot_relative_path(filepath)
        file_status = self._client.status(rel_path)
        for s in file_status:
            if s.type == svn.constants.ST_UNVERSIONED:
                self._client.add(rel_path)
                break
            if s.type == svn.constants.ST_MISSING:
                self._client.remove(rel_path)
                break
        if filepath not in self._staged_files:
            self._staged_files.append(p.normpath(filepath))

    def request_unstage(self, filepath):
        """Remove the input file from staging.

        Throws ValueError if value wasn't staged.
    
        request_unstage(str) -> None
        """
        assert p.isabs(filepath)
        self._staged_files.remove(p.normpath(filepath))
        rel_path = self._to_svnroot_relative_path(filepath)
        file_status = self._client.status(rel_path)
        for s in file_status:
            if s.type == svn.constants.ST_ADDED:
                # self._client.revert doesn't exist. Since we're calling svn
                # directly, use the absolute path.
                r = self._client.run_command('revert', [filepath])
                print(r)
            # In theory, we could auto revert+delete when unstaging a deleted
            # file, but it's safer to just remove it from the staged files and
            # let the user revert.
            # if s.type == svn.constants.ST_DELETED:
            #     can_delete = not p.exists(filepath)
            #     r = self._client.run_command('revert', [filepath])
            #     if can_delete:
            #         # Only delete if it didn't exist on disk -- that means svn restored it.
            #         os.remove(filepath)
            #     print(r)
            #     break

    def is_staged(self, filepath):
        """Check if a file is staged to be committed.

        is_staged(str) -> boolean
        """
        assert p.isabs(filepath)
        # Normalize to ensure irrelevant differences in filepaths
        # don't cause false negatives.
        return p.normpath(filepath) in self._staged_files

    def _get_stage_status(self):
        """Get the status repo's staged files.
    
        _get_stage_status() -> list(str), list(str), list(str)
        """
        staged    = []
        unstaged  = []
        listed    = []
        untracked = []
        root_len = len(self._root_dir) + 1
        for status in self._client.status():
            if self.is_staged(status.name):
                staged.append(status)
            elif status.type == svn.constants.ST_NORMAL or status.changelist == 'ignore-on-commit':
                # Ignore normal files. They should only show up from changelists.
                # Ignore 'ignore-on-commit' changelist. This is a TortoiseSVN
                # convention for a commit you never commit from.
                continue
            elif status.type == svn.constants.ST_UNVERSIONED:
                untracked.append(status)
            elif status.changelist:
                listed.append(status)
            else:
                unstaged.append(status)

        return staged, unstaged, listed, untracked


    def _get_stage_status_text(self, fmt, headers):
        """Get the status repo's staged files.
    
        _get_stage_status_text() -> str, str, str
        """

        def convert(h,c,title):
            return [h.format(count=len(c), title=title)] + [fmt(status) for status in c]

        def convert_cl(h,c):
            grouped = {status.changelist : [] for status in c}
            for status in c:
                grouped[status.changelist].append(status)
            # merge lists for each group of changelists into one.
            sorted_keys = sorted(grouped.keys())
            lines = itertools.chain.from_iterable(convert(h,grouped[title],title) for title in sorted_keys)
            return list(lines)

        staged, unstaged, listed, untracked = self._get_stage_status()
        staged, unstaged, untracked = [convert(headers[i],c,None) for i,c in enumerate([staged, unstaged, untracked])]
        listed = convert_cl(headers[-1],listed)

        def _join_if_has_files(files):
            if len(files) > 1:
                return "\n".join(files) + "\n"
            return ""
        staged, unstaged, listed, untracked = [_join_if_has_files(x) for x in [staged, unstaged, listed, untracked]]
        return staged, unstaged, listed, untracked


    def _commit_text(self):
        def fmt(status):
            # Print in this style:
            #	new file:   pythonx/sovereign.py
            return '#\t{}:\t{}'.format(status.type_raw_name, self._to_svnroot_relative_path(status.name))

        headers = [
            '#\n# Changes to be committed:',
            '#\n# Changes not staged for commit:',
            '#\n# Untracked files:',
            # changelist must be last
            '#\n# Changelist[{title}] not staged for commit:',
        ]
        staged, unstaged, listed, untracked = self._get_stage_status_text(fmt, headers)
        diff = "\n".join([self._unified_diff(staged_file, 'HEAD', '') for staged_file in self._staged_files])
        txt = f'''
# Please enter the commit message for your changes. Lines starting
# with '#' will be ignored, and an empty message aborts the commit.
#
# On branch {self.get_branch()}
{staged}{unstaged}{untracked}
{listed}#
# {_SNIP_MARKER}
# Do not modify or remove the line above.
# Everything below it will be ignored.
{diff}'''
        return txt

    def _unified_diff(self, full_url_or_path, old, new):
        # self._client.diff() doesn't work since it tries to give us the diff
        # in a list and I don't want to put it back together again.
        try:
            d = self._client.run_command(
                'diff',
                ['--git',
                 '--old', '{0}@{1}'.format(full_url_or_path, old),
                 '--new', '{0}@{1}'.format(full_url_or_path, new),
                 ],
                do_combine=True)
        except svn.exception.SvnException as e:
            # I think this error only occurs on windows? I'm not actually
            # seeing this output, but this prevents errors that stops Scommit
            # from working.
            return f"New file: {full_url_or_path}\n" + str(e)
        # skip 'Index:' line and '===' line.
        return trim_leading_lines(d, 2)

    def commit(self, commit_msg_file):
        """Commit current changes using message from input file-object

        commit(File) -> None
        """
        if not self._staged_files:
            return False, "No files staged to commit"

        commit_msg_lines = commit_msg_file.readlines()

        error_empty_msg = 'Aborting commit due to empty commit message'

        if not commit_msg_lines:
            return False, error_empty_msg

        for i,line in enumerate(commit_msg_lines):
            if _SNIP_MARKER in line:
                commit_msg_lines = commit_msg_lines[:i-1]
                break

        commit_msg_lines = [line for line in commit_msg_lines if line[0] != '#']

        if all([line.isspace() for line in commit_msg_lines]):
            return False, error_empty_msg

        message = "".join(commit_msg_lines)
        try:
            self._client.commit(message, self._staged_files)
        except svn.exception.SvnException as e: 
            return False, str(e)

        # Unfortunately, commit doesn't return anything so we need to lookup
        # the revision ourselves.
        #
        # svn doesn't know how to show log for deleted files without
        # revision it last existed, so only attempt ones that exist.
        try:
            relpath = next(self._to_svnroot_relative_path(filepath) for filepath in self._staged_files if p.exists(filepath))
        except StopIteration as e:
            relpath = None
            pass
        # Clear staging now that they're submitted.
        self._staged_files.clear()
        if relpath:
            try:
                log = self._client.log_default(rel_filepath=relpath, limit=1)
                for line in log:
                    # Return the first (should be only) result.
                    revision = line.revision
                    return True, 'Committed revision {}.'.format(line.revision)
            except svn.exception.SvnException as e:
                # Getting the revision isn't important, so ignore failures.
                pass
        return True, 'Committed unknown revision'

    def update(self, single_file=None, revision=None):
        """Get latest revision from server
    
        update() -> None
        """
        if not single_file:
            single_file = [single_file]
        else:
            single_file = []
        self._client.update(single_file, revision)

    def _cat_file_unprocessed(self, filepath, revision):
        rel_path = self._to_svnroot_relative_path(filepath)
        f = self._client.cat(rel_filepath=rel_path, revision=revision)
        # svn.client.cat returns binary output, so it doesn't convert to
        # unicode, but we assume all files we cat will be text files that can
        # be unicode.
        f = f.decode('utf8')
        # Will have an incorrect trailing space!
        return f

    def cat_file(self, filepath, revision):
        f = self._cat_file_unprocessed(filepath, revision)
        # Remove incorrect trailing space character
        if f[-1].isspace():
            f = f[:-1]
        return f

    def cat_file_as_list(self, filepath, revision):
        assert p.isabs(filepath)
        # Assume repo holds files in windows-style \r\n because vim won't
        # represent \r as a line ending even with ff=dos.
        # (We could strip \r line endings, but splitting on line endings once
        # seems more correct.)
        f = self._cat_file_unprocessed(filepath, revision)
        processed = f.split('\r\n')
        if len(processed) < 2:
            # No match means it's not crlf. Assume local os line endings.
            processed = f.split(os.linesep)
        if len(processed) < 2:
            # No match means we're on Windows, but it's not crlf. Assume unix line endings.
            processed = f.split('\n')
        f = processed
        # svn emits a trailing \r. When line endings are \r\n, it sometimes
        # results in an empty line at the end and sometimes is cleaned up by
        # the split. When line endings are \n, it's a line with an \r. Either
        # way, try to clean the extra line.
        if f[-1].isspace() or len(f[-1]) == 0:
            f = f[:-1]
        return f

    def get_log_text(self, filepath, limit=10, include_diff=True, revision_from=None, revision_to=None, query=None):
        """Get log buffer text for log
    
        log(str, int) -> str
        """
        assert p.isabs(filepath)

        log = self._client.log_default(
            rel_filepath = self._to_svnroot_relative_path(filepath),
            limit = limit,
            revision_from = revision_from,
            revision_to = revision_to,
            search = query,
        )

        full_url_or_path = filepath

        if include_diff:
            def get_diff(entry):
                try:
                    return self._unified_diff(full_url_or_path, entry.revision-1, entry.revision)
                except svn.SvnException as e:
                    return str(e)
        else:
            def get_diff(entry):
                return ''
        

        qf_items = [{
            'filecontents': '''r{revision}
Author: {author}
Date:   {date}

{msg}

{diff}
            '''.format(
                revision = entry.revision,
                author = entry.author,
                date = format_datetime(entry.date),
                msg = _prefix_lines(entry.msg, ' '), # prefix to prevent syntax highlight
                diff = get_diff(entry),
            ),
            'col': 0,
            'lnum': 0,
            'module': f'r{entry.revision}',
            'nr': 0,
            'pattern': '',
            'text': _take_first_x_lines(entry.msg, 1),
            'type': '',
            'valid': 1,
            'vcol': 0,
        } for entry in log]
        return qf_items


    def get_buffer_name_for_file(self, filepath, revision):
        assert p.isabs(filepath)
        rel_path = self._to_svnroot_relative_path(filepath)
        i = self._client.info(rel_path=rel_path, revision=revision)
        name = i['url']
        colon = name.find(':')
        assert colon > 0, "Expected url always includes a protocol"
        return 'sovereign' + name[colon:]


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
    allow_commit = False # True

    # Useful for debugging status()
    def get_all_attr(item):
        return [a for a in dir(item) if a[0] != '_' and a not in ['count', 'index']]
    def print_status(status):
        if not status:
            return
        for s in status:
            names = [a for a in get_all_attr(s)]
            names = {a : getattr(s, a) for a in names}
            pp.pprint(names)

    # Create the svn repo with:
    #   repo=/Users/idbrii/data/code/svntest/repo
    #   svnadmin create $repo
    #   svn mkdir --parents -m"Creating basic directory structure" file://$repo/trunk file://$repo/branches file://$repo/tags
    #   svn checkout file://$repo/trunk checkout
    import io, os, datetime
    repo_root = p.expanduser('~/data/code/svntest/checkout/')
    os.chdir(repo_root)

    hello = p.join(repo_root, 'hello')
    r = get_repo(hello)

    modified_by_test = p.join(repo_root, 'modified_by_test')
    nestedhi = p.join(repo_root, 'subdir/nestedhi')
    trailnewline = p.join(repo_root, 'subdir/hastrailingnewline')
    file_for_cl1 = p.join(repo_root, 'subdir/file_for_cl1')
    file_for_cl2 = p.join(repo_root, 'subdir/file_for_cl2')
    files = [hello, modified_by_test, nestedhi, trailnewline, file_for_cl1, file_for_cl2]
    if not all(p.isfile(f) for f in files):
        if allow_commit:
            # Setup test case
            subdir = p.join(repo_root, 'subdir')
            os.makedirs(subdir, exist_ok=True)
            r.request_stage(subdir)
            for fpath in files:
                with open(fpath, 'w', encoding='utf8') as f:
                    f.write("hello\n") 
                r.request_stage(fpath)
            r.commit(io.StringIO("setup repo\n\nlonger message goes here\n"))
            print('Created test svn repo.')
        else:
            print('Error: test svn repo not correctly setup. please enable allow_commit')
        return
    

    for fname in [modified_by_test, file_for_cl1, file_for_cl2]:
        with open(fname, 'w', encoding='utf8') as f:
            f.write("modifying this file\n") 
            f.write(str(datetime.datetime.now())) 
            f.write("\n") 

    r._client.run_command('changelist', ['my-cl', file_for_cl1])
    r._client.run_command('changelist', ['another-cl', file_for_cl2])

    print('Stage: Before staging some files')
    pp.pprint(r._staged_files)
    print()
    r.request_stage(modified_by_test)
    r.request_stage(nestedhi)
    print('Stage: After staging some files')
    pp.pprint(r._staged_files)
    print()
    print()

    print('Sstatus')
    print(r._status_text())
    print()
    print('sovereign#branch()')
    print(r.get_branch())
    print()

    print('Scommit buffer')
    print(r._commit_text())
    print()
    if allow_commit:
        print('Scommit complete')
        pp.pprint(r.commit(io.StringIO("Commit from test\n\nlonger message goes here\n{}".format(r._commit_text()))))
        print()

    print('Sstatus')
    print(r._status_text())
    print()

    print('Sdiff')
    print(r.cat_file(trailnewline, 'HEAD'))
    print()

    print('Slog', hello)
    log = r.get_log_text(None)
    print(log)
    print(log[0]['filecontents'])
    print('Slog', repo_root)
    log = r.get_log_text(repo_root)
    print(log)
    print(log[0]['filecontents'])
    # hist = r._client.log_default(rel_filepath='hello', limit=1)
    # for h in hist:
    #     pp.pprint(h)
    print()

    print('Stage: After unstaging some files')
    if not allow_commit:
        r.request_unstage(modified_by_test)
        r.request_unstage(nestedhi)
    pp.pprint(r._staged_files)

    r._client.run_command('changelist', ['--remove', file_for_cl1])
    r._client.run_command('changelist', ['--remove', file_for_cl2])

    print()
    print('done')



if __name__ == "__main__":
    test()
