pyx import sovereign.vimapi as sovereignapi

if has('win32')
    " python interprets "\U" in "C:\Users" as a unicode escape sequence and
    " barfs on the function call (not even inside the function), so it can't
    " get any backslashes in path names. Assume only win32 is dumb enough to
    " pass paths like that and allow other platforms to use escapes.
    function! s:to_unix_path_sep(path)
        return substitute(a:path, '\\', '/', 'g')
    endf
else
    function! s:to_unix_path_sep(path)
        return a:path
    endf
endif

" Our vimapi requires absolute paths and Python requires them in unix format.
function! s:to_python_safe_path(path)
    return resolve(fnamemodify(s:to_unix_path_sep(a:path), ':p'))
endf

" No args means default -- current buffer.
function! s:get_safe_path_from_args(args)
    if len(a:args) == 0
        " For empty a:000 or empty str use current.
        let path = expand('%')
    elseif type(a:args) == type([])
        let path = expand(a:args[0])
    else
        let path = expand(a:args)
    endif
    return s:to_python_safe_path(path)
endf

function! s:pyeval(cmd)
    try
        call pyxeval(a:cmd)
        return v:true
    catch
        " In theory we want to catch this error:
        " /^Vim\%((\a\+)\)\=:E858/	" Eval did not return a valid python object
        " But using that regex catches nothing. Partly because the error
        " doesn't register as a vim error (it's not prefixed with Vim). Maybe
        " also because there's too much in the callstack.

        " Fallback to v:exception in case we failed to catch in python.
        let error = get(g:, 'sovereign_exception', v:exception)
        echohl WarningMsg | echomsg error | echohl None
        silent! unlet g:sovereign_exception
        return v:false
    endtry
endf

function! s:to_py_bool(vim_bool) abort
    if a:vim_bool
        return 'True'
    endif
    return 'False'
endf

function! s:create_scratch(split_cmd, bufname)
    if exists(':ScratchNoSplit') == 2
        exec a:split_cmd
        silent ScratchNoSplit
    elseif exists(':Scratch') == 2
        silent Scratch
    else
        " TODO: This needs testing.
        silent exec a:split_cmd .' '. a:bufname
        setlocal buftype=nofile
        setlocal bufhidden=hide
        setlocal noswapfile
        setlocal buflisted
    endif

    if len(a:bufname) > 0
        call execute('file '. a:bufname)
    endif
endf

function! sovereign#branch_name() abort
    " Only update branch every 5 seconds
    if !exists('s:sovereign_branch_lastupdate')
        let s:sovereign_branch_lastupdate = localtime()
    elseif localtime() - s:sovereign_branch_lastupdate < 5
        return s:sovereign_branch_cached
    endif
    
    let path = s:to_python_safe_path('%')
    let cmd = printf('sovereignapi.get_branch("%s")', path)
    if !s:pyeval(cmd)
        return '--'
    endif
    let s:sovereign_branch_cached = g:sovereign_returnvalue
    unlet g:sovereign_returnvalue
    return s:sovereign_branch_cached
endfunction

function! sovereign#status() abort
    let path = s:to_python_safe_path('%')
    call s:create_scratch('split', 'sovereign-status')
    let cmd = printf('sovereignapi.setup_buffer_status("%s")', path)
    if !s:pyeval(cmd)
        bdelete
        return
    endif
    setfiletype sovereign
endfunction

function! sovereign#stage(...) abort
    let path = s:get_safe_path_from_args(a:000)

    let cmd = printf('sovereignapi.stage_file("%s")', path)
    if !s:pyeval(cmd)
        return
    endif
endfunction

function! sovereign#commit(...) abort
    let path = s:get_safe_path_from_args(a:000)

    let f = s:to_python_safe_path(tempname() . '_commit')
    call execute('split '. f)
    wincmd _
    " We copy git formatting, so use their syntax.
    setfiletype gitcommit
    let cmd = printf('sovereignapi.setup_buffer_commit("%s", "%s")', path, f)
    if !s:pyeval(cmd)
        return
    endif
endfunction

function! sovereign#diff(...) abort
    let revision = ''
    let path = s:get_safe_path_from_args(a:000)
    if len(a:000) > 1
        let revision = a:000[1]
    endif

    let old_ft = &l:filetype
    call s:create_scratch('vsplit', '')
    let &l:filetype = old_ft
    let cmd = printf('sovereignapi.setup_buffer_cat("%s", "%s")', path, revision)
    if !s:pyeval(cmd)
        bdelete
        return
    endif
    " TODO: depends on diffusable
    DiffBoth
endfunction

function! sovereign#log(limit, showdiff, ...) abort
    let path = s:get_safe_path_from_args(a:000)
    let g:sovereign_scratch = a:000[1:]

    let cmd = printf('sovereignapi.setup_buffer_log("%s", %i, %s, "sovereign_scratch")', path, a:limit, s:to_py_bool(a:showdiff))
    if !s:pyeval(cmd)
    endif
    unlet g:sovereign_scratch
endfunction

function! sovereign#edit() abort
    if !s:pyeval('sovereignapi.jump_to_originator()')
        return
    endif
endfunction
