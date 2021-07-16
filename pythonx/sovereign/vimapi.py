#! /usr/bin/env python3

import collections
import functools
import os
import os.path as p
import re
import traceback

import vim
import sovereign.repo as repo


def capture_exception(ex):
    """Store exception for later handling.

    capture_exception(Exception) -> None
    """
    ex_name = type(ex).__name__
    ex_msg = str(ex)
    vim.vars['sovereign_exception'] = "%s: %s" % (ex_name, ex_msg)
    vim.vars['sovereign_callstack'] = traceback.format_exc().split('\n')


def vim_error_on_fail(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            capture_exception(ex)
            # Fire error so we can catch failure in vimscript.
            vim.command('echoerr g:sovereign_exception')
            return None
    return wrapper


@vim_error_on_fail
def dbg_repo():
    '''Get the current buffer -- for interactive debugging from vim.
    '''
    b = vim.current.buffer
    return _get_repo(b.name, b)


def clamp(minimum, x, maximum):
    return max(minimum, min(x, maximum))

repos = {}
def _get_repo(filepath, buffer):
    try:
        return repos[buffer]
    except KeyError:
        r = repo.get_repo(filepath)
        repos[buffer] = r
        return r

tempfile_to_repo = {}
def _get_repo_for_tempfile(temp_filepath):
    # Use realpath to ensure this key will match the input one.
    temp_filepath = p.realpath(temp_filepath)
    return tempfile_to_repo[temp_filepath]

def _set_repo_for_tempfile(temp_filepath, repo):
    temp_filepath = p.realpath(temp_filepath)
    tempfile_to_repo[temp_filepath] = repo




def _extra_quote_strings(t):
    if type(t) == str:
        return f"""'{t}'"""
    else:
        return str(t)
    
def _func_args(args, kwargs):
    out = ''
    if args:
        args = [_extra_quote_strings(a) for a in args]
        out = f""", {', '.join(args)}"""

    if kwargs:
        out += ', ' + ', '.join(f"""{k}={_extra_quote_strings(v)}""" for k,v in kwargs.items())

    return out

def _nmap(key, funcname, *args, **kwargs):
    args = _func_args(args, kwargs)
    # passes (linenum, line, ...) to funcname. linenum is the 0-index line
    # number in the buffer so vim.current.buffer[linenum] == line. (Vim uses
    # 1-indexing.)
    vim.command(f'''nnoremap <buffer> {key} :<C-u>call pyxeval(printf("sovereignapi.{funcname}(%i, r'%s'{args})", line(".")-1, getline(".")))<CR>''')

def _vmap(key, funcname, *args, **kwargs):
    args = _func_args(args, kwargs)
    # passes (startline, endline, ...) to funcname. firstline and lastline is
    # the 0-index line number in the buffer so vim.current.buffer[linenum] ==
    # line. (Vim uses 1-indexing.)
    vim.command(f'''xnoremap <buffer> {key} :<C-u>call pyxeval(printf("sovereignapi.{funcname}(%i, %s{args})", line("'<")-1, line("'>")-1))<CR>''')

def _autocmd(group, event, pattern, funcname, args=None):
    args = _func_args(args, None)
    vim.command(r'augroup '+ group)
    if pattern == '<buffer>':
        vim.command(r'    au! * <buffer>')
    else:
        vim.command(r'    au!')
    vim.command(r'    autocmd {event} {pattern} call pyxeval("sovereignapi.{funcname}(\'". expand("<amatch>:p") {args} ."\')")'.format(**locals()))
    vim.command(r'augroup END')

def _create_scratch_buffer(contents, filetype, originating_filepath, should_stay_open):
    vim.command('new')
    vim.command('setlocal buftype=nofile bufhidden=hide noswapfile buflisted')
    if filetype:
        vim.command('setfiletype '+ filetype)
    vim.current.buffer[:] = contents
    vim.current.buffer.vars['sovereign_originator'] = originating_filepath
    bufnr = vim.eval('bufnr()')
    if not should_stay_open:
        vim.command('close')
    return bufnr


# statusline {{{1

@vim_error_on_fail
def get_branch(filepath):
    r = _get_repo(filepath, vim.current.buffer)
    branch = '--'
    if r:
        branch = r.get_branch()
    vim.vars['sovereign_returnvalue'] = branch


# Sstatus {{{1

@vim_error_on_fail
def setup_buffer_status(filepath):
    r = _get_repo(filepath, vim.current.buffer)
    if not r:
        vim.eval(f'echo "{filepath}" is not in svn')
        return None
    
    b = vim.current.buffer
    _set_buffer_text_status(b, r)

    _autocmd('sovereign', 'BufEnter', '<buffer>', 'status_refresh')

    # Copying the interface from fugitive so it's familiar to fugitive users
    # (like me).
    _nmap('<C-N>', 'change_item_no_expand', 1)
    _nmap('<C-P>', 'change_item_no_expand', -1)

    _nmap('<CR>',  'edit', 'edit')
    _nmap('o',     'edit', 'split')
    _nmap('O',     'edit', 'tabedit')
    _nmap('gO',    'edit', 'vsplit')

    _nmap('c',     'commit', verbose=True)
    _nmap('dd',    'diff_item', manage_win=True)
    # _nmap('dq',          'diff_close')

    # fugitive uses - for stage toggle, but I prefer s. easy to reach key and
    # more useful than separate stage/unstage.
    _nmap('s',     'status_stage_unstage')
    _vmap('s',         'status_stage_unstage_range')
    _nmap('-',     'status_stage_unstage')
    _vmap('-',         'status_stage_unstage_range')
    _nmap('a',     'status_stage_unstage')
    # _nmap('u',           'unstage')

    _nmap('R',           'status_refresh')

    _nmap('.',           'populate_cmdline')
    _vmap('.',           'populate_cmdline_range')

    # _nmap('p',           'GF_pedit')
    # _nmap('<',           'InlineDiff_hide')
    # _nmap('>',           'InlineDiff_show')
    # _nmap('=',           'InlineDiff_toggle')

    # _nmap('J',           'jump_to_next_hunk')
    # _nmap('K',           'jump_to_prev_hunk')
    # _nmap('i',           'next_item_no_expand')
    # _nmap(']/',          'next_item')
    # _nmap('[/',          'PreviousFile')
    # _nmap(']m',          'next_item')
    # _nmap('[m',          'PreviousFile')
    # _nmap('(',           'prev_item_expand')
    # _nmap(')',           'next_item_expand')

    # _nmap(']]',          'NextSection')
    # _nmap('[[',          'PreviousSection')
    # _nmap('][',          'NextSectionEnd')
    # _nmap('[]',          'PreviousSectionEnd')

    return None


def _set_buffer_text_status(buf, repo):
    buf.options['modifiable'] = True
    buf[:] = repo._status_text().split('\n')
    buf.options['modifiable'] = False
    buf.options['bufhidden'] = 'delete'
    buf.vars['sovereign_type'] = 'index'

def change_item_no_expand(linenum, line, direction):
    num_buf_lines = len(vim.current.buffer)
    i = linenum + direction
    while 0 <= i < num_buf_lines:
        line = vim.current.buffer[i]
        if line and line[0].isupper():
            break
        i += direction

    # convert to 1-indexed and clamp
    i = clamp(1, i + 1, num_buf_lines)

    w = vim.current.window
    c = w.cursor
    w.cursor = (i, c[1])


def _get_status_block_end(start):
    total_lines = len(vim.current.buffer)
    for linenum in range(start + 1, total_lines):
        line = vim.current.buffer[linenum]
        if not line or line.isspace() or is_status_header(line):
            return linenum - 1
    raise IndexError(f"Error: Selection didn't get the same start? start={start}")

def _get_abs_filepath_from_line(line, r):
    if not line or line.isspace():
        # these might eval to '.' and cause badness
        return None
    file_start = line.find(' ')
    rel_path = line[file_start+1:]
    abs_path = r.relative_to_absolute(rel_path)
    if p.isabs(abs_path):
        return abs_path
    return None

def _escape_filename(filepath):
    # Vim expands # and %
    return re.sub("([#%])", r"\\\1", filepath)

def edit(linenum, line, how):
    """Edit the file in the previous window.

    edit(int, str, str) -> None
    """
    r = repos[vim.current.buffer]
    filepath = _get_abs_filepath_from_line(line, r)
    vim.command('wincmd p')
    vim.command(how +' '+ _escape_filename(filepath))

def _prepare_svn_cmdline(r, cmd):
    vim.vars['sovereign_scratch'] = cmd
    os.chdir(r._root_dir)
    vim.eval('feedkeys(":\<C-r>=g:sovereign_scratch\<CR>\<Home>! svn  \<Left>")')
    # We have to leave sovereign_scratch dangling because we can't send another command.

def _quote(strs):
    return [f'"{s}"' for s in strs]

def populate_cmdline(linenum, line):
    """Open vim cmdline with svn and current file pre populated.

    Ideally, this would use :Svn which more nicely collects results from svn,
    but that command doesn't exist.

    populate_cmdline(int, str) -> None
    """
    r = repos[vim.current.buffer]
    if not line or line.isspace():
        print("WARN: Invalid line to start cmdline")
        return
    if is_status_header(line):
        start = linenum + 1
        end = _get_status_block_end(start)
        populate_cmdline_range(start, end)
        return

    filepath = _get_abs_filepath_from_line(line, r)
    _prepare_svn_cmdline(r, f'"{filepath}"')

def populate_cmdline_range(start, end):
    """Open vim cmdline with svn and current file pre populated.

    Ideally, this would use :Svn which more nicely collects results from svn,
    but that command doesn't exist.

    populate_cmdline(int, str) -> None
    """
    if start > end:
        raise IndexError("Error: Populate cmdline doesn't support backward ranges.")

    r = repos[vim.current.buffer]
    b = vim.current.buffer
    files = []
    for linenum in range(start, end+1):
        line = b[linenum]
        if not line or line.isspace() or is_status_header(line):
            # Skip over invalid lines so we can get our entire selection.
            # Selecting a header does not select everything in that heading.
            continue
        
        abs_path = _get_abs_filepath_from_line(line, r)
        files.append(abs_path)

    _prepare_svn_cmdline(r, " ".join(_quote(files)))

def commit(linenum, line, verbose=True):
    # TODO: Would be nice to stay within python, but some of the buf creation
    # stuff is in vim (and maybe it's easier in vim so maybe there's no point).
    cmd = 'Scommit '
    # if verbose:
    #     cmd += '-v'
    vim.command(cmd)

def diff_item(linenum, line, manage_win):
    status_b = vim.current.buffer
    status_b.vars['sovereign_block_refresh'] = True

    # preserve height, but limit to show more diff
    win_height = int(vim.eval(f'winheight(".")'))
    desired_height = vim.options['lines'] * 0.2
    win_height = min(win_height, desired_height)

    num_win = int(vim.eval('winnr("$")'))
    if num_win != 2:
        # If we had a previous diff, we need to close it. If we had some other
        # windows, there's not enough space to diff. If we're the only window,
        # we need a split.
        # TODO: Better to re-use existing layout? Or open a tab?
        # Fugitive seems to go back to the previous window, load the file,
        # split, diff.
        vim.command('only')
        # Destination for diff
        vim.command('split')
    
    edit(linenum, line, 'silent botright edit')
    # vim.command('resize') # full height
    vim.command('Sdiff')

    winnr = vim.eval(f'bufwinnr({status_b.number})')
    vim.command(winnr +'wincmd w')
    status_b.vars['sovereign_block_refresh'] = False

    vim.command(f'resize {win_height:.0f}')


def is_status_header(line):
    return line[1] != ' '

def status_stage_unstage(linenum, line):
    r = repos[vim.current.buffer]
    is_valid = line and not line.isspace()
    if not is_valid:
        return
    
    if is_status_header(line):
        # Get everything in block
        try:
            # LIMIT(safety): Limit stage 10 files at a time to avoid runaway failures.
            start = linenum + 1
            end = min(start + 10, _get_status_block_end(start))
            for linenum in range(start, end + 1):
                line = vim.current.buffer[linenum]
                abs_path = _get_abs_filepath_from_line(line, r)
                if not abs_path:
                    break
                r.request_stage_toggle(abs_path)
        except IndexError:
            pass
    else:
        abs_path = _get_abs_filepath_from_line(line, r)
        r.request_stage_toggle(abs_path)


@vim_error_on_fail
def status_stage_unstage_range(start, end):
    if start > end:
        raise IndexError("Error: Stage doesn't support backward ranges.")

    r = repos[vim.current.buffer]
    b = vim.current.buffer
    for linenum in range(start, end+1):
        line = b[linenum]
        if not line or line.isspace() or is_status_header(line):
            # Skip over non file lines so we can stage our entire selection.
            # Selecting a header does not stage everything in that heading.
            continue
        
        abs_path = _get_abs_filepath_from_line(line, r)
        r.request_stage_toggle(abs_path)

    _set_buffer_text_status(b, r)


def status_refresh(*_):
    r = repos[vim.current.buffer]
    b = vim.current.buffer
    if not b.vars.get('sovereign_block_refresh', False):
        _set_buffer_text_status(b, r)


# Sadd {{{1

@vim_error_on_fail
def stage_file(filepath):
    r = _get_repo(filepath, vim.current.buffer)
    r.request_stage(filepath)


# Scommit {{{1

@vim_error_on_fail
def create_buffer_commit(filepath, commit_msg_filepath):
    if not commit_msg_filepath:
        print('ERROR: Failed to get valid commit scratch file')
        return None

    r = _get_repo(filepath, vim.current.buffer)
    if not r._staged_files:
        print('No files staged to commit')
        return None

    vim.command('split '+ commit_msg_filepath)
    vim.command('wincmd _')
    # We copy git formatting, so use their syntax.
    vim.command("setfiletype gitcommit")

    _set_repo_for_tempfile(commit_msg_filepath, r)
    b = vim.current.buffer
    # We don't delete the buffer (don't know how to do that from BufWinLeave),
    # so just leave it unlisted.
    b.vars['&buflisted'] = 0
    # Ale causes errors, so ignore them.
    b.vars['ale_enabled'] = 0
    # Save empty file to ensure no changes results in failure to commit.
    b[:] = []
    vim.command('update')
    b[:] = r._commit_text().split('\n')
    _autocmd('sovereign', 'BufWinLeave', '<buffer>', 'on_close_commit_buffer')
    return None

def on_close_commit_buffer(commit_msg_filepath):
    """Actually trigger the commit.

    on_close_commit_buffer(str) -> None
    """
    vim.command('au! sovereign * <buffer>')
    r = _get_repo_for_tempfile(commit_msg_filepath)
    try:
        with open(commit_msg_filepath, 'r') as f:
            success, msg = r.commit(f)
            if success:
                print(msg)
            else:
                err_list = msg.split('\n')
                if len(err_list) == 1:
                    print(err_list[0])
                else:
                    vim.command('tabnew')
                    _create_scratch_buffer(
                        err_list + ['', '', '', "Commit message file:", '   '+ commit_msg_filepath],
                        None,
                        commit_msg_filepath,
                        should_stay_open=True)
                    vim.command('setlocal bufhidden=wipe')
                    vim.command('file commit-error')
    except FileNotFoundError:
        print('Aborting commit due to empty commit message.')


# Sdiff {{{1

@vim_error_on_fail
def setup_buffer_cat(filepath, revision):
    if not revision or revision == 'HAVE':
        # Default to HAVE revision.
        revision = None

    r = _get_repo(filepath, vim.current.buffer)
    b = vim.current.buffer
    b[:] = r.cat_file_as_list(filepath, revision)
    b.options['modifiable'] = False
    b.options['bufhidden'] = 'delete'
    b.name = r.get_buffer_name_for_file(filepath, revision)
    return None


# Sclog {{{1

@vim_error_on_fail
def setup_buffer_log(filepath, limit, showdiff, dest_prefix, args_var):
    """
    setup_buffer_log(string, int, int, string, string) -> None
    """
    r = _get_repo(filepath, vim.current.buffer)
    log_args = [s.decode('utf-8') for s in vim.vars[args_var]]
    log_args = " ".join(log_args)
    qf_items = r.get_log_text(filepath, limit=limit, include_diff=showdiff, query=log_args)
    items = []

    old_lazyredraw = vim.options['lazyredraw']
    for commit in qf_items:
        # TODO:
        # * Add svndiff format that's based on diff, but lets you navigate
        #   revisions? fugitive has 'git' filetype.
        # * Make navigating the quickfix use the same window like fugitive. Not
        #   sure how? It uses bufhidden=delete instead of hide.
        # * Load diff on buffer load instead of buffer creation (to speed up processing).
        commit['bufnr'] = _create_scratch_buffer(commit['filecontents'].split('\n'), 'diff', filepath, should_stay_open=False)

    vim.options['lazyredraw'] = old_lazyredraw

    qf_what = { 'items': qf_items }
    qf_what['title'] = ':Slog '+ filepath

    # log == [{
    # 'filecontents': '\nr9\nauthor dbriscoe Sun, 09 Feb 2020 06:32:54 +0000\n\nfrom vim\n\n\ndiff --git a/hello b/hello\n--- a/hello\t(revision 8)\n+++ b/hello\t(revision 9)\n@@ -1,3 +1,4 @@\n hello\n hi there\n hi again\n+and more content\n\n',
    # 'col': 0,
    # 'lnum': 0,
    # 'module': 9,
    # 'nr': 0,
    # 'pattern': '',
    # 'text': 'from vim\n',
    # 'type': '',
    # 'valid': 1,
    # 'vcol': 0
    # },

    if dest_prefix == 'c':
        dest_fn = 'setqflist('
    else:
        dest_fn = 'setloclist(0,'
    vim.vars['sovereign_qf_scratch'] = vim.Dictionary(qf_what)
    vim.eval(f'{dest_fn}[], " ", g:sovereign_qf_scratch)')
    # vim.command('unlet g:sovereign_qf_scratch')
    vim.command(f'{dest_prefix}open')

# Sedit {{{1

@vim_error_on_fail
def jump_to_originator():
    try:
        originator = vim.current.buffer.vars['sovereign_originator'].decode('utf-8')
        vim.command('edit '+ _escape_filename(originator))
    except KeyError:
        # do nothing if we don't have an originator
        pass

@vim_error_on_fail
def setup_show_revision(filepath, revision):
    """
    setup_show_revision(str, str) -> None
    """
    b = vim.current.buffer
    r = _get_repo(filepath, b)
    items = r.get_log_text(filepath, limit=1, include_diff=True, revision_from=revision, revision_to=revision)
    if items:
        contents = items[0]['filecontents'].split('\n')
    else:
        # Either invalid revision or it doesn't exist in our branch.
        #
        # Need to create an LocalClient from the url instead of local path to
        # see changes from other branches. That's a bunch of work that doesn't
        # currently seem worthwhile right now.
        # url = r._client.info()['repository/root']
        contents = [f'Failed to find revision r{revision}']
    
    bufnr = _create_scratch_buffer(contents, 'diff', filepath, should_stay_open=False)
    # We close and then open it so it replaces the current buffer and we can
    # see more of it.
    vim.command(f'buffer {bufnr}')

# }}}
