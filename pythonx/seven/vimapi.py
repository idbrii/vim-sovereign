#! /usr/bin/env python3

import os.path as p

import vim
import seven.repo as repo

repos = {}

def _map(mode, key, funcname, args=None):
    if args:
        args = ', '+ args
    else:
        args = ''
    vim.command('{}noremap <buffer> {} :<C-u>call pyxeval("sevenapi.{}(". line(".") .", \'". getline(".") ."\'" {} .")")<CR>'.format(mode, key, funcname, args))


# Sstatus {{{1

def setup_buffer_status(filepath):
    r = repo.get_repo(filepath)
    b = vim.current.buffer
    b[:] = r._status_text().split('\n')
    b.options['modifiable'] = False
    b.vars['fugitive_type'] = 'index'
    repos[vim.current.buffer] = r

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

    _map('n', 's',     'stage_unstage') # my remap. more useful than separate stage/unstage.
    _map('n', '-',     'stage_unstage')
    _map('n', 'a',     'stage_unstage')
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

def stage_unstage(linenum, line):
    r = repos[vim.current.buffer]
    # TODO: If already staged, then unstage.
    r.request_stage(_get_file_from_line(line))


# Scommit {{{1

def setup_buffer_commit(filepath):
    r = repo.get_repo(filepath)
    b = vim.current.buffer
    b[:] = r._commit_text().split('\n')
    # TODO: mappings
    return None

# Sdiff

def setup_buffer_cat(filepath, revision):
    r = repo.get_repo(filepath)
    b = vim.current.buffer
    b[:] = r.cat_file(filepath, revision).split('\n')
    b.options['modifiable'] = False
    b.name = r.get_buffer_name_for_file(filepath, revision)
    return None


# }}}
