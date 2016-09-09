# coding: yupp

($__TITLE__)

($import stdlib)

($dict VAR
	(` NAME        DEFVAL     FORMAT  )
	(`
	(  var_string  "calgary"  "%s"    )
	(  var_float   19.88      "%.2f"  )
	(  var_int     46         "%d"    )
	)
)

($each-VAR \i.]
	($i NAME) = ($i DEFVAL)

[ )

if __name__ == '__main__':
	($each-VAR \i.]
		print ($q,,($i NAME) = ($unq ($i FORMAT))) % ( ($i NAME) )

	[ )
