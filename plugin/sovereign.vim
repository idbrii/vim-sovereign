if exists('loaded_sovereign') || &cp || version < 700 || !exists("*pyxeval")
    finish
endif
let loaded_sovereign = 1


" Sstatus always show *repo* status. Pass a path to change the targetted repo.
command! -bar -nargs=* -complete=file Sstatus call sovereign#status(<q-args>)
command! -bar -nargs=* Sadd call sovereign#stage(<f-args>)
command! -bar Scommit call sovereign#commit()
command! -bar -nargs=* Sdelete call sovereign#delete(<bang>0, <f-args>)
command! -bar -nargs=* Sdiff call sovereign#diff(<f-args>)

" Hide diff if bang is included.
command! -bar -nargs=* -count=10 -bang Sclog call sovereign#log(<count>, <bang>1, 'c', <f-args>)
command! -bar -nargs=* -count=10 -bang Sllog call sovereign#log(<count>, <bang>1, 'l', <f-args>)

" No Args: go back to normal file (if known)
" With Args: pass a revision and we'll show its details
command! -bar -nargs=? Sedit call sovereign#edit(<q-args>)
