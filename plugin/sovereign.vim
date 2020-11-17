if exists('loaded_sovereign') || &cp || version < 700 || !exists("*pyxeval")
    finish
endif
let loaded_sovereign = 1


command! Sstatus call sovereign#status()
command! -nargs=* Sadd call sovereign#stage(<f-args>)
command! -nargs=* Scommit call sovereign#commit(<f-args>)
command! -nargs=* Sdiff call sovereign#diff(<f-args>)
command! -count=10 Slog call sovereign#log(<count>)
command! Sedit call sovereign#edit()
