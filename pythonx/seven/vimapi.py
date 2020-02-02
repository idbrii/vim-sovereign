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
    _map('n', 'c',     'commit', 'verbose=True')
    _map('n', 'dd',    'diff_item')
    _map('n', 's',     'stage_unstage') # my remap. more useful than separate stage/unstage.
    _map('n', '-',     'stage_unstage')

    # Wow fugitive has a lot of mappings. Not sure if I'll support all of
    # these.

    # _map('n', '-',           'Do_Toggle')
    # _map('n', 'a',           'Do_Toggle')
    # _map('n', 'u',           'Do_Unstage')
    # _map('n', 'U',           'EchoExec_reset')
    # _map('n', 'p',           'GF_pedit')
    # _map('n', '<',           'StageInline_hide')
    # _map('n', '>',           'StageInline_show')
    # _map('n', '=',           'StageInline_toggle')
    # _map('n', 'D',           'diff_item') # deprecated
    # _map('n', '.',           'edit_from_cmdline')
    # _map('n', 'o',           'edit_in_split')
    # _map('n', 'O',           'edit_in_tab')
    # _map('n', 'J',           'jump_to_next_hunk')
    # _map('n', 'K',           'jump_to_prev_hunk')
    # _map('n', ')',           'next_item_expand')
    # _map('n', 'i',           'next_item_no_expand')
    # _map('n', '*',           'patch_search_next')
    # _map('n', '#',           'patch_search_prev')
    # _map('n', '(',           'prev_item_expand')
    # _map('n', 'R',           'refresh')
    # _map('n', '~',           'show_ancestor')
    # _map('n', 'dp',          &@:<C-U>execute fugitive - StageDiffEdit()<CR>
    # _map('n', 'g?',          &@:<C-U>help fugitive-map<CR>
    # _map('n', 'd?',          &@:<C-U>help fugitive_d<CR>
    # _map('n', 'gq',          &@:<C-U>if bufnr('$') == 1|quit|else|bdelete|endif<CR>
    # _map('n', 'gC',          '??')
    # _map('n', 'gc',          '??')
    # _map('n', ']]',          'NextSection')
    # _map('n', '][',          'NextSectionEnd')
    # _map('n', '[/',          'PreviousFile')
    # _map('n', '[m',          'PreviousFile')
    # _map('n', '[[',          'PreviousSection')
    # _map('n', '[]',          'PreviousSectionEnd')
    # _map('n', 'dh',          'StageDiff_Ghdiffsplit')
    # _map('n', 'ds',          'StageDiff_Ghdiffsplit')
    # _map('n', 'dv',          'StageDiff_Gvdiffsplit')
    # _map('n', 'gi',          'check_ignore')
    # _map('n', 'dq',          'diff_close')
    # _map('n', 'gO',          'edit_in_vsplit')
    # _map('n', 'gf',          'fancy_gf')
    # _map('n', ']c',          'jump_to_next_hunk')
    # _map('n', '[c',          'jump_to_prev_hunk')
    # _map('n', ']/',          'next_item')
    # _map('n', ']m',          'next_item')
    # _map('n', 'ce',          *@:<C-U>Gcommit --amend --no-edit<CR>
    # _map('n', 'cw',          *@:<C-U>Gcommit --amend --only<CR>
    # _map('n', 'ca',          *@:<C-U>Gcommit --amend<CR>
    # _map('n', 'cA',          *@:<C-U>Gcommit --edit --squash=<C-R>=fugitive - SquashArgument()<CR>
    # _map('n', 'cf',          *@:<C-U>Gcommit --fixup=<C-R>=fugitive - SquashArgument()<CR>
    # _map('n', 'cs',          *@:<C-U>Gcommit --no-edit --squash=<C-R>=fugitive - SquashArgument()<CR>
    # _map('n', 'cc',          *@:<C-U>Gcommit<CR>
    # _map('n', 'ra',          *@:<C-U>Grebase --abort<CR>
    # _map('n', 'rf',          *@:<C-U>Grebase --autosquash<C-R>=fugitive - RebaseArgument()<CR><CR>
    # _map('n', 'rr',          *@:<C-U>Grebase --continue<CR>
    # _map('n', 're',          *@:<C-U>Grebase --edit-todo<CR>
    # _map('n', 'rp',          *@:<C-U>Grebase --interactive @{push}<CR>
    # _map('n', 'ru',          *@:<C-U>Grebase --interactive @{upstream}<CR>
    # _map('n', 'ri',          *@:<C-U>Grebase --interactive<C-R>=fugitive - RebaseArgument()<CR><CR>
    # _map('n', 'rd',          *@:<C-U>Grebase --interactive<C-R>=fugitive - RebaseArgument()<CR>|s/^pick/drop/e<CR>
    # _map('n', 'rk',          *@:<C-U>Grebase --interactive<C-R>=fugitive - RebaseArgument()<CR>|s/^pick/drop/e<CR>
    # _map('n', 'rx',          *@:<C-U>Grebase --interactive<C-R>=fugitive - RebaseArgument()<CR>|s/^pick/drop/e<CR>
    # _map('n', 'rm',          *@:<C-U>Grebase --interactive<C-R>=fugitive - RebaseArgument()<CR>|s/^pick/edit/e<CR>
    # _map('n', 'rw',          *@:<C-U>Grebase --interactive<C-R>=fugitive - RebaseArgument()<CR>|s/^pick/reword/e<CR>
    # _map('n', 'rs',          *@:<C-U>Grebase --skip<CR>
    # _map('n', 'c?',          *@:<C-U>help fugitive_c<CR>
    # _map('n', 'r?',          *@:<C-U>help fugitive_r<CR>
    # _map('n', 'cF',          *@:<C-U>|Grebase --autosquash<C-R>=fugitive - RebaseArgument()<CR><Home>Gcommit --fixup=<C-R>=<SNR>363_SquashArgument()<CR>
    # _map('n', 'cS',          *@:<C-U>|Grebase --autosquash<C-R>=fugitive - RebaseArgument()<CR><Home>Gcommit --no-edit --squash=<C-R>=<SNR>363_SquashArgument()<CR>
    # _map('n', 'cRe',         *@:<C-U>Gcommit --reset-author --amend --no-edit<CR>
    # _map('n', 'cRw',         *@:<C-U>Gcommit --reset-author --amend --only<CR>
    # _map('n', 'cRa',         *@:<C-U>Gcommit --reset-author --amend<CR>
    # _map('n', 'cva',         *@:<C-U>Gcommit -v --amend<CR>
    # _map('n', 'cvc',         *@:<C-U>Gcommit -v<CR>
    # _map('n', 'crn',         *@:<C-U>Grevert --no-commit <C-R>=fugitive - SquashArgument()<CR><CR>
    # _map('n', 'crc',         *@:<C-U>Grevert <C-R>=fugitive - SquashArgument()<CR><CR>
    # _map('n', 'czv',         *@:<C-U>exe 'Gedit' fugitive#RevParse('stash@{' . v:count . '}')<CR>
    # _map('n', 'czz',         *@:<C-U>exe fugitive - EchoExec(['stash'] + (v:count > 1 ? ['--all'] : v:count ? ['--include-untracked'] : []))<CR>
    # _map('n', 'cb?',         *@:<C-U>help fugitive_cb<CR>
    # _map('n', 'co?',         *@:<C-U>help fugitive_co<CR>
    # _map('n', 'cz?',         *@:<C-U>help fugitive_cz<CR>
    # _map('n', 'coo',         *@:exe fugitive - EchoExec(['checkout'] + split(<SNR>363_SquashArgument()) + ['--'])<CR>
    # _map('n', 'cm?',         *@:help fugitive_cm<CR>
    # _map('n', 'cr?',         *@:help fugitive_cr<CR>
    # _map('n', '<F1>',        *@:call <SNR>388_PrintGitStatusHelp()<CR>
    # _map('n', '<C-L>',        @R<Plug>(david-redraw-screen)<Space>
    # _map('n', 'c<CR>',       'git_commit')
    # _map('n', 'r<CR>',       'git_rebase')
    # _map('n', '<C-W>f',       @fugitive - :sfind <Plug><cfile><CR>
    # _map('n', 'cv<CR>',      'Git_commit')
    # _map('n', 'cb<CR>',      'git_branch')
    # _map('n', 'co<CR>',      'git_checkout')
    # _map('n', 'cm<CR>',      'git_merge')
    # _map('n', 'cr<CR>',      'git_revert')
    # _map('n', 'cz<CR>',      'git_stash')
    # _map('n', '<C-W>gf',      @fugitive - :tabfind <Plug><cfile><CR>
    # _map('n', 'c<Space>',    'git_commit')
    # _map('n', 'r<Space>',    'git_rebase')
    # _map('n', 'cv<Space>',   'Git_commit')
    # _map('n', 'cb<Space>',   'git_branch')
    # _map('n', 'co<Space>',   'git_checkout')
    # _map('n', 'cm<Space>',   'git_merge')
    # _map('n', 'cr<Space>',   'git_revert')
    # _map('n', 'cz<Space>',   'git_stash')
    # _map('n', '<C-W><C-F>',   @fugitive - :sfind <Plug><cfile><CR>
    # _map('n', 'czw',         *@:<C-U>exe fugitive - EchoExec(['stash', '--keep-index'] + (v:count > 1 ? ['--all'] : v:count ? ['--include-untracked'] : []))<CR>
    # _map('n', '<2-LeftMouse>', 'GF_edit')
    # _map('n', 'gr',          &@:<C-U>exe fugitive - StageJump(v:count, 'Rebasing')<CR>
    # _map('n', 'gs',          &@:<C-U>exe fugitive - StageJump(v:count, 'Staged')<CR>
    # _map('n', 'gP',          &@:<C-U>exe fugitive - StageJump(v:count, 'Unpulled')<CR>
    # _map('n', 'gp',          &@:<C-U>exe fugitive - StageJump(v:count, 'Unpushed')<CR>
    # _map('n', 'gu',          &@:<C-U>exe fugitive - StageJump(v:count, 'Untracked', 'Unstaged')<CR>
    # _map('n', 'gU',          &@:<C-U>exe fugitive - StageJump(v:count, 'Unstaged', 'Untracked')<CR>
    # _map('n', 'czA',         *@:<C-U>exe fugitive - EchoExec(['stash', 'apply', '--quiet', 'stash@{' . v:count . '}'])<CR>
    # _map('n', 'czP',         *@:<C-U>exe fugitive - EchoExec(['stash', 'pop', '--quiet', 'stash@{' . v:count . '}'])<CR>
    # _map('n', 'cza',         *@:<C-U>exe fugitive - EchoExec(['stash', 'apply', '--quiet', '--index', 'stash@{' . v:count . '}'])<CR>
    # _map('n', 'czp',         *@:<C-U>exe fugitive - EchoExec(['stash', 'pop', '--quiet', '--index', 'stash@{' . v:count . '}'])<CR>
    # _map('n', 'X',           &@:<C-U>execute fugitive - StageDelete(line('.'), 0, v:count)<CR>
    # _map('n', 'gI',          &@:<C-U>execute fugitive - StageIgnore(line('.'), line('.'), v:count)<CR>
    # _map('n', 'I',           &@:<C-U>execute fugitive - StagePatch(line('.'),line('.'))<CR>
    # _map('n', 'P',           &@:<C-U>execute fugitive - StagePatch(line('.'),line('.')+v:count1-1)<CR>

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
