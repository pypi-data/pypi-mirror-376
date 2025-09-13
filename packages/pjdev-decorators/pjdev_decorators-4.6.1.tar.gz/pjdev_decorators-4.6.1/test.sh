#!/bin/bash
uv sync --active --extra test
export PYTHONPATH=./src:./tests
pytest tests/*.py
