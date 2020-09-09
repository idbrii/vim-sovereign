#! /usr/bin/env python3

import collections
import functools
import os.path as p

import vim
import sovereign.repo as repo


def capture_exception(ex):
    """Store exception for later handling.

    capture_exception(Exception) -> None
    """
    ex_name = type(ex).__name__
    ex_msg = str(ex)
    vim.vars['sovereign_exception'] = "%s: %s" % (ex_name, ex_msg)


def vim_error_on_fail(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            capture_exception(ex)
            # Fire error so we can catch failure in vimscript.
            vim.command(f'echoerr g:sovereign_exception')
            return None
    return wrapper


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




def _func_args(args):
    if args:
        return ', '+ args
    else:
        return ''

def _map(mode, key, funcname, args=None):
    args = _func_args(args)
    vim.command('{}noremap <buffer> {} :<C-u>call pyxeval("sovereignapi.{}(". line(".") .", \'". getline(".") ."\'" {} .")")<CR>'.format(mode, key, funcname, args))

def _autocmd(group, event, pattern, funcname, args=None):
    args = _func_args(args)
    vim.command(r'augroup '+ group)
    if pattern == '<buffer>':
        vim.command(r'    au! * <buffer>')
    else:
        vim.command(r'    au!')
    vim.command(r'    autocmd {event} {pattern} call pyxeval("sovereignapi.{funcname}(\'". expand("<amatch>:p") {args} ."\')")'.format(**locals()))
    vim.command(r'augroup END')

def _create_scratch_buffer(contents, filetype, should_stay_open):
    vim.command('new')
    vim.command('setlocal buftype=nofile bufhidden=hide noswapfile buflisted')
    if filetype:
        vim.command('setfiletype '+ filetype)
    vim.current.buffer[:] = contents
    bufnr = vim.eval('bufnr()')
    if not should_stay_open:
        vim.command('close')
    return bufnr


# Sstatus {{{1

@vim_error_on_fail
def setup_buffer_status(filepath):
    r = _get_repo(filepath, vim.current.buffer)
    if not r:
        vim.eval(f'echo "{filepath}" is not in svn')
        return None
    
    b = vim.current.buffer
    _set_buffer_text_status(b, r)

    # Copying the interface from fugitive so it's familiar to fugitive users
    # (like me).
    _map('n', '<C-N>', 'change_item_no_expand', '1')
    _map('n', '<C-P>', 'change_item_no_expand', '-1')

    _map('n', '<CR>',  'edit', 'edit')
    # _map('n', 'o',           'edit_in_split')
    # _map('n', 'O',           'edit_in_tab')
    # _map('n', 'gO',          'edit_in_vsplit')

    _map('n', 'c',     'commit', 'verbose=True')
    _map('n', 'dd',    'diff_item')
    # _map('n', 'dq',          'diff_close')

    _map('n', 's',     'status_stage_unstage') # my remap. more useful than separate stage/unstage.
    _map('n', '-',     'status_stage_unstage')
    _map('n', 'a',     'status_stage_unstage')
    # _map('n', 'u',           'unstage')

    # _map('n', 'R',           'refresh')

    # _map('n', '.',           'edit_from_cmdline')

    # _map('n', 'p',           'GF_pedit')
    # _map('n', '<',           'InlineDiff_hide')
    # _map('n', '>',           'InlineDiff_show')
    # _map('n', '=',           'InlineDiff_toggle')

    # _map('n', 'J',           'jump_to_next_hunk')
    # _map('n', 'K',           'jump_to_prev_hunk')
    # _map('n', 'i',           'next_item_no_expand')
    # _map('n', ']/',          'next_item')
    # _map('n', '[/',          'PreviousFile')
    # _map('n', ']m',          'next_item')
    # _map('n', '[m',          'PreviousFile')
    # _map('n', '(',           'prev_item_expand')
    # _map('n', ')',           'next_item_expand')

    # _map('n', ']]',          'NextSection')
    # _map('n', '[[',          'PreviousSection')
    # _map('n', '][',          'NextSectionEnd')
    # _map('n', '[]',          'PreviousSectionEnd')

    return None


def _set_buffer_text_status(buf, repo):
    buf.options['modifiable'] = True
    buf[:] = repo._status_text().split('\n')
    buf.options['modifiable'] = False
    buf.options['bufhidden'] = 'delete'
    buf.vars['fugitive_type'] = 'index'

def change_item_no_expand(linenum, direction):
    w = vim.current.window
    c = w.cursor
    w.cursor = (c[0] + direction, c[1])


def _get_file_from_line(line):
    file_start = line.find(' ')
    return line[file_start+1:]

def edit(linenum, line, how):
    """Edit the file in the previous window.

    edit(int, str, str) -> None
    """
    r = repos[vim.current.buffer]
    filepath = p.join(r._root_dir, _get_file_from_line(line))
    vim.command('wincmd p')
    vim.command(how +' '+ filepath)

def commit(linenum, line, verbose=True):
    # TODO: Would be nice to stay within python, but some of the buf creation
    # stuff is in vim (and maybe it's easier in vim so maybe there's no point).
    cmd = 'Scommit '
    if verbose:
        cmd += '-v'
    vim.command(cmd)

def diff_item(linenum, line):
    # TODO: Do I want to split? I think I want to switch to the buffer if it's
    # in a visible window and open the diff, otherwise open a tab? Or replace
    # an existing window? Maybe the previous one?
    # Fugitive seems to go back to the previous window, load the file, split,
    # diff.
    edit(linenum, line, 'silent botright edit')
    # vim.command('resize') # full height
    vim.command('Sdiff')

def status_stage_unstage(linenum, line):
    r = repos[vim.current.buffer]
    r.request_stage_toggle(_get_file_from_line(line))
    _set_buffer_text_status(vim.current.buffer, r)


# Sadd {{{1

@vim_error_on_fail
def stage_file(filepath):
    r = _get_repo(filepath, vim.current.buffer)
    r.request_stage(filepath)


# Scommit {{{1

@vim_error_on_fail
def setup_buffer_commit(filepath, commit_msg_filepath):
    r = _get_repo(filepath, vim.current.buffer)
    _set_repo_for_tempfile(commit_msg_filepath, r)
    b = vim.current.buffer
    b[:] = r._commit_text().split('\n')
    # When buffer is closed, it's deleted because we set bufhidden=delete,
    # BufDelete is fired and BufHidden is not.
    b.options['bufhidden'] = 'delete'
    _autocmd('sovereign', 'BufDelete', '<buffer>', 'on_close_commit_buffer')
    return None

def on_close_commit_buffer(commit_msg_filepath):
    """Actually trigger the commit.

    on_close_commit_buffer(str) -> None
    """
    r = _get_repo_for_tempfile(commit_msg_filepath)
    try:
        with open(commit_msg_filepath, 'r') as f:
            success, msg = r.commit(f)
            print(msg)
    except FileNotFoundError:
        print('Aborting commit due to empty commit message.')


# Sdiff {{{1

@vim_error_on_fail
def setup_buffer_cat(filepath, revision):
    r = _get_repo(filepath, vim.current.buffer)
    b = vim.current.buffer
    b[:] = r.cat_file(filepath, revision).split('\n')
    b.options['modifiable'] = False
    b.options['bufhidden'] = 'delete'
    b.name = r.get_buffer_name_for_file(filepath, revision)
    return None


# Slog {{{1

@vim_error_on_fail
def setup_buffer_log(filepath, limit):
    """
    setup_buffer_log(string, int, int) -> None
    """
    r = _get_repo(filepath, vim.current.buffer)
    qf_items = r.get_log_text(filepath, limit=limit)
    items = []

    old_lazyredraw = vim.options['lazyredraw']
    for commit in qf_items:
        # TODO:
        # * Add svndiff format that's based on diff, but lets you navigate
        #   revisions? fugitive has 'git' filetype.
        # * Make navigating the quickfix use the same window like fugitive. Not
        #   sure how? It uses bufhidden=delete instead of hide.
        commit['bufnr'] = _create_scratch_buffer(commit['filecontents'].split('\n'), 'diff', should_stay_open=False)

    vim.options['lazyredraw'] = old_lazyredraw

    qf_what = { 'items': qf_items }

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

    vim.vars['sovereign_qf_scratch'] = vim.Dictionary(qf_what)
    vim.eval('setqflist([], " ", g:sovereign_qf_scratch)')
    vim.command('unlet g:sovereign_qf_scratch')

# }}}
