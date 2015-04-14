if exists('g:loaded_undodb')
	finish
endif
let g:loaded_undodb = 1

py3 import undodb
autocmd BufWritePost * py3 undodb.write()
command Undo py3 undodb.read()
