.PHONY: run test evaluate check site ci

run:
	python3 app.py

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

evaluate:
	PYTHONPATH=src python3 -m market_radar.cli run
	PYTHONPATH=src python3 -m market_radar.cli evaluate

check:
	python3 scripts/check_repository.py

site:
	PYTHONPATH=src python3 scripts/build_static_site.py

ci: test check
