#pylint: skip-file
import os
import sublime, sublime_plugin

class OpenSourceCommand( sublime_plugin.TextCommand ):
    def run( self, edit ):
        fn = self.view.file_name()
        if fn:
            b, e = os.path.splitext( fn )
            fn_yu = b + '.yu'
            if e:
                fn_yu += '-' + e[ 1: ]
            if os.path.isfile( fn_yu ):
                view = self.view.window().open_file( fn_yu )
