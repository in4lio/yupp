TEMPLATE = app
TARGET = glance
INCLUDEPATH += .
CONFIG += console
DESTDIR = ./
OBJECTS_DIR = ./

PP = python -u ../../yup.py
PP_FLAGS = -q --pp-browse -Wno-unbound
PP_SOURCES = glance.yu-cpp

pp.name = Preprocessing .yu-cpp files
pp.input = PP_SOURCES
pp.output = ${QMAKE_FILE_BASE}.cpp
pp.commands = $$PP $$PP_FLAGS ${QMAKE_FILE_IN}
pp.variable_out = SOURCES

QMAKE_EXTRA_COMPILERS += pp
