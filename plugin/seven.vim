if exists('loaded_seven') || &cp || version < 700
    finish
endif
let loaded_seven = 1


command! Sstatus call seven#status()
command! Scommit call seven#commit()
command! Sdiff call seven#diff()
