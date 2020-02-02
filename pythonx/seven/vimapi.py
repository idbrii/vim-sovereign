#! /usr/bin/env python3

import vim
import seven.repo as repo

def status(filepath):
    r = repo.get_repo(filepath)
    b = vim.current.buffer
    b[:] = r._status_text().split('\n')
    b.options['modifiable'] = False
    b.vars['fugitive_type'] = 'index'
    # TODO: mappings
    return None


def commit(filepath):
    r = repo.get_repo(filepath)
    b = vim.current.buffer
    b[:] = r._commit_text().split('\n')
    # TODO: mappings
    return None


def cat(filepath, revision):
    r = repo.get_repo(filepath)
    b = vim.current.buffer
    b[:] = r.cat_file(filepath, revision).split('\n')
    b.options['modifiable'] = False
    b.name = r.get_buffer_name_for_file(filepath, revision)
    return None


