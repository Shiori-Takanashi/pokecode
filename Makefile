.PHONY: all pokecode flask set

pokecode:
	uv run python -m pokecode.main

flask:
	uv run python server/app.py
