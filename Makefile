.PHONY: all pokecode flask set

set:
	uv run python -m server.app & \
		sleep 1; \
		uv run python -m pokecode.main

pokecode:
	uv run python -m pokecode.main

flask:
	uv run python -m server.app
