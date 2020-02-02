pyx import seven.vimapi as sevenapi

function! s:create_scratch()
    if exists(':Scratch') == 2
        Scratch
    else
        vnew
        setlocal buftype=nofile
        setlocal bufhidden=hide
        setlocal noswapfile
        setlocal buflisted
    endif
endf

function! seven#status() abort
    let path = expand('%')
    call s:create_scratch()
    "~ let b:fugitive_type = 'index'
    let cmd = printf('sevenapi.setup_buffer_status("%s")', path)
    call pyxeval(cmd)
    setfiletype fugitive
endfunction

function! seven#commit(...) abort
    if len(a:000) == 0
        let path = expand('%')
    else
        let path = a:000[0]
    endif

    call s:create_scratch()
    setfiletype gitcommit
    let cmd = printf('sevenapi.setup_buffer_commit("%s")', path)
    call pyxeval(cmd)
endfunction

function! seven#diff(...) abort
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
    call s:create_scratch()
    let &l:filetype = old_ft
    let cmd = printf('sevenapi.setup_buffer_cat("%s", "%s")', path, revision)
    let g:DAVID_test = cmd
    call pyxeval(cmd)
    " TODO: depends on diffusable
    DiffBoth
endfunction

