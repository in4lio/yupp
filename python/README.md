### How to start using `yupp` with Python 2

1. Install Python package:
```
pip install yupp
```

2. Start your code on Python with:
```
# coding: yupp
```
for example:
```
# coding: yupp
# test.py

($set hola 'Hello world!')
print ($hola)
```

3. Run the script in the usual way:
```
python ./test.py

Hello world!
```

### How to use `yupp` with Python 3

1. Process your script with `yupp`:
```
python yup.py -q ./test.yu-py
```

2. Run the preprocessed script:
```
python ./test.py
```

### See also

[Configure Sublime Text](../sublime_text/)

[More examples](../eg/)
