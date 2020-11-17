if exists('loaded_sovereign') || &cp || version < 700 || !exists("*pyxeval")
    finish
endif
let loaded_sovereign = 1


command! Sstatus call sovereign#status()
command! -nargs=* Sadd call sovereign#stage(<f-args>)
command! -nargs=* Scommit call sovereign#commit(<f-args>)
command! -nargs=* Sdiff call sovereign#diff(<f-args>)
" Hide diff if bang is included.
command! -nargs=* -count=10 -bang Slog call sovereign#log(<count>, <q-args>, <bang>1)
command! Sedit call sovereign#edit()
