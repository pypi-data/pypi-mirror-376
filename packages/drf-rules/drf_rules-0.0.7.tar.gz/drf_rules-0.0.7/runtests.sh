#!/bin/sh

# NOTE: Make sure you `pip install -e .` first
coverage run tests/manage.py test --failfast -v2 testapp "$@" \
  && echo \
  && coverage report -m
