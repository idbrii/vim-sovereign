pyx import sovereign.vimapi as sovereignapi

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
        echohl WarningMsg | echomsg g:sovereign_exception | echohl None
        return v:false
    endtry
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

function! sovereign#status() abort
    let path = expand('%')
    call s:create_scratch('split', 'sovereign-status')
    "~ let b:fugitive_type = 'index'
    let cmd = printf('sovereignapi.setup_buffer_status("%s")', path)
    if !s:pyeval(cmd)
        bdelete
        return
    endif
    setfiletype fugitive
endfunction

function! sovereign#stage(...) abort
    if len(a:000) == 0
        let path = expand('%')
    else
        let path = a:000[0]
    endif

    let cmd = printf('sovereignapi.stage_file("%s")', path)
    if !s:pyeval(cmd)
        return
    endif
endfunction

function! sovereign#commit(...) abort
    if len(a:000) == 0
        let path = expand('%:p')
    else
        let path = fnamemodify(a:000[0], ':p')
    endif

    let f = tempname() . '_commit'
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
    let revision = 'HEAD'
    if len(a:000) == 0
        let path = expand('%')
    elseif len(a:000) == 1
        let path = a:000[0]
    else
        let path = a:000[0]
        let revision = a:000[0]
    endif

    let path = fnamemodify(path, ':p')

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

function! sovereign#log(limit) abort
    let path = expand('%:p')

    let cmd = printf('sovereignapi.setup_buffer_log("%s", %i)', path, a:limit)
    if !s:pyeval(cmd)
        return
    endif
endfunction
