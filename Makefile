ENVDIR = env

MKDIR ?= mkdir -p
RM ?= rm -f
RMDIR ?= rm -fr
VIRTUALENV ?= pyvenv

PIP = $(ENVDIR)/bin/pip
PYTHON = $(ENVDIR)/bin/python


.PHONY: environment clean dist-clean maintainer-clean build_sphinx sdist flake8 test doc

environment: $(ENVDIR)/installed

$(ENVDIR)/installed: $(PIP) dev-requirements.txt requirements.txt test-requirements.txt
	$(PIP) install -r dev-requirements.txt
	$(PIP) freeze > "$@"

$(PIP): $(PYTHON)
$(PYTHON):
	$(VIRTUALENV) $(ENVDIR)

clean:
	- $(RMDIR) build
	- $(RMDIR) *.egg-info
	- $(RM) .coverage

dist-clean: clean
	- $(RMDIR) dist
	- $(RM) $(ENVDIR)/installed

maintainer-clean: dist-clean
	- $(RMDIR) $(ENVDIR)

build_sphinx flake8 sdist test: environment
	$(ENVDIR)/bin/python setup.py $@

doc: build_sphinx
