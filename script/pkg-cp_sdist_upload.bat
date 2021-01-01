@echo off

set home=%~dp0..\

rem ---- pp ----

xcopy /Y %home%\README %home%\package\
xcopy /Y %home%\LICENSE %home%\package\

xcopy /Y %home%\__main__.py %home%\package\yupp\
xcopy /Y %home%\__init__.py %home%\package\yupp\
xcopy /Y %home%\pp\yup.py %home%\package\yupp\pp\
xcopy /Y %home%\pp\yugen.py %home%\package\yupp\pp\
xcopy /Y %home%\pp\yuconfig.py %home%\package\yupp\pp\
xcopy /Y %home%\pp\yulic.py %home%\package\yupp\pp\

xcopy /Y %home%\pylib\__init__.py %home%\package\yupp\pylib\
xcopy /Y %home%\pylib\yutraceback.py %home%\package\yupp\pylib\

rem ---- lib ----

xcopy /Y %home%\lib\corolib.yu %home%\package\yupp\lib\corolib.yu
xcopy /Y %home%\lib\coroutine-h.yu %home%\package\yupp\lib\coroutine-h.yu
xcopy /Y %home%\lib\coroutine-py.yu %home%\package\yupp\lib\coroutine-py.yu
xcopy /Y %home%\lib\coroutine.h %home%\package\yupp\lib\coroutine.h
xcopy /Y %home%\lib\coroutine.yu %home%\package\yupp\lib\coroutine.yu
xcopy /Y %home%\lib\h-light.yu %home%\package\yupp\lib\h-light.yu
xcopy /Y %home%\lib\h.yu %home%\package\yupp\lib\h.yu
xcopy /Y %home%\lib\hlib.yu %home%\package\yupp\lib\hlib.yu
xcopy /Y %home%\lib\stdlib.yu %home%\package\yupp\lib\stdlib.yu

rem ---- uninstall ----

echo y | python -m pip uninstall yupp

rem ---- sdist, upload ----

python setup.py sdist upload

pause
