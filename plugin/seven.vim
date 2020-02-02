if exists('loaded_seven') || &cp || version < 700 || !exists("*pyxeval")
    finish
endif
let loaded_seven = 1


command! Sstatus call seven#status()
command! -nargs=* Scommit call seven#commit(<f-args>)
command! -nargs=* Sdiff call seven#diff(<f-args>)
