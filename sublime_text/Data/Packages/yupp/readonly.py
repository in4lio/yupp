import os
import sublime
import sublime_plugin

class readonly( sublime_plugin.EventListener ):
    def on_activated( self, view ):
        fn = view.file_name()
        if fn:
            view.set_read_only( not os.access( fn, os.W_OK ))
