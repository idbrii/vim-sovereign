" Based on vim-fugitive/syntax/fugitive.vim.
" Copyright (c) Tim Pope.  Distributed under the same terms as Vim itself.
" See `:help license`.
if exists("b:current_syntax")
  finish
endif

syn sync fromstart
syn spell notoplevel

syn include @sovereignDiff syntax/diff.vim

syn match sovereignHeader /^[A-Z][a-z][^:]*:/ nextgroup=sovereignHash,sovereignSymbolicRef skipwhite
syn match sovereignBareHeader /^Bare:/
syn match sovereignHelpHeader /^Help:/ nextgroup=sovereignHelpTag skipwhite
syn match sovereignHelpTag    /\S\+/ contained

syn region sovereignSection start=/^\%(.*(\d\+)$\)\@=/ contains=sovereignHeading end=/^$/
syn cluster sovereignSection contains=sovereignSection
syn match sovereignHeading /^[A-Z][a-z][^:]*\ze (\d\+)$/ contains=sovereignPreposition contained nextgroup=sovereignCount skipwhite
syn match sovereignCount /(\d\+)/hs=s+1,he=e-1 contained
syn match sovereignPreposition /\<\%([io]nto\|from\|to\|Rebasing\%( detached\)\=\)\>/ transparent contained nextgroup=sovereignHash,sovereignSymbolicRef skipwhite

syn match sovereignInstruction /^\l\l\+\>/ contained containedin=@sovereignSection nextgroup=sovereignHash skipwhite
syn match sovereignDone /^done\>/ contained containedin=@sovereignSection nextgroup=sovereignHash skipwhite
syn match sovereignStop /^stop\>/ contained containedin=@sovereignSection nextgroup=sovereignHash skipwhite
syn match sovereignModifier /^[MADRCU?]\{1,2} / contained containedin=@sovereignSection
syn match sovereignSymbolicRef /\.\@!\%(\.\.\@!\|[^[:space:][:cntrl:]\:.]\)\+\.\@<!/ contained
syn match sovereignHash /^\x\{4,\}\S\@!/ contained containedin=@sovereignSection
syn match sovereignHash /\S\@<!\x\{4,\}\S\@!/ contained

syn region sovereignHunk start=/^\%(@@\+ -\)\@=/ end=/^\%([A-Za-z?@]\|$\)\@=/ contains=@sovereignDiff containedin=@sovereignSection fold

for s:section in ['Untracked', 'Unstaged', 'Staged']
  exe 'syn region sovereign' . s:section . 'Section start=/^\%(' . s:section . ' .*(\d\+)$\)\@=/ contains=sovereign' . s:section . 'Heading end=/^$/'
  exe 'syn match sovereign' . s:section . 'Modifier /^[MADRCU?] / contained containedin=sovereign' . s:section . 'Section'
  exe 'syn cluster sovereignSection add=sovereign' . s:section . 'Section'
  exe 'syn match sovereign' . s:section . 'Heading /^[A-Z][a-z][^:]*\ze (\d\+)$/ contains=sovereignPreposition contained nextgroup=sovereignCount skipwhite'
endfor
unlet s:section

hi def link sovereignBareHeader sovereignHeader
hi def link sovereignHelpHeader sovereignHeader
hi def link sovereignHeader Label
hi def link sovereignHelpTag Tag
hi def link sovereignHeading PreProc
hi def link sovereignUntrackedHeading PreCondit
hi def link sovereignUnstagedHeading Macro
hi def link sovereignStagedHeading Include
hi def link sovereignModifier Type
hi def link sovereignUntrackedModifier StorageClass
hi def link sovereignUnstagedModifier Structure
hi def link sovereignStagedModifier Typedef
hi def link sovereignInstruction Type
hi def link sovereignStop Function
hi def link sovereignHash Identifier
hi def link sovereignSymbolicRef Function
hi def link sovereignCount Number

let b:current_syntax = "sovereign"
