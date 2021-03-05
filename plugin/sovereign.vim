if exists('loaded_sovereign') || &cp || version < 700 || !exists("*pyxeval")
    finish
endif
let loaded_sovereign = 1


" Sstatus always show *repo* status. Pass a path to change the targetted repo.
command! -nargs=* -complete=file Sstatus call sovereign#status(<q-args>)
command! -nargs=* Sadd call sovereign#stage(<f-args>)
command! -nargs=* Scommit call sovereign#commit(<f-args>)
command! -nargs=* Sdiff call sovereign#diff(<f-args>)
" Hide diff if bang is included.
command! -nargs=* -count=10 -bang Slog call sovereign#log(<count>, <bang>1, <f-args>)
command! Sedit call sovereign#edit()
