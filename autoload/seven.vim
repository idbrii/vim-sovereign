pyx import seven.vimapi as sevenapi

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

function! seven#status() abort
    let path = expand('%')
    call s:create_scratch('split', 'seven-status')
    "~ let b:fugitive_type = 'index'
    let cmd = printf('sevenapi.setup_buffer_status("%s")', path)
    call pyxeval(cmd)
    setfiletype fugitive
endfunction

function! seven#stage(...) abort
    if len(a:000) == 0
        let path = expand('%')
    else
        let path = a:000[0]
    endif

    let cmd = printf('sevenapi.stage_file("%s")', path)
    call pyxeval(cmd)
endfunction

function! seven#commit(...) abort
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
    let cmd = printf('sevenapi.setup_buffer_commit("%s", "%s")', path, f)
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
    call s:create_scratch('vsplit', '')
    let &l:filetype = old_ft
    let cmd = printf('sevenapi.setup_buffer_cat("%s", "%s")', path, revision)
    call pyxeval(cmd)
    " TODO: depends on diffusable
    DiffBoth
endfunction

function! seven#log(limit) abort
    let path = expand('%:p')

    let cmd = printf('sevenapi.setup_buffer_log("%s", %i)', path, a:limit)
    call pyxeval(cmd)
endfunction
