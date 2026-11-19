PY ?= python3

.PHONY: verify test gen baselines analysis mutation fuzz explain

# ЕДИНАЯ КОМАНДА ПРОВЕРКИ: сертификаты эпизодов, контракт, награда, мутации, парные проверки,
# изолированный прогон всех политик, скоркард по рубрике жюри. Без сети, API и GPU.
verify:
	$(PY) -m auditforge.cli verify
	$(PY) -m pytest -q

test:
	$(PY) -m pytest -q

gen:
	$(PY) -m auditforge.cli gen

baselines:
	$(PY) -m auditforge.cli baselines

analysis:
	$(PY) -m auditforge.cli analysis

mutation:
	$(PY) -m auditforge.cli mutation

fuzz:
	$(PY) -m auditforge.cli fuzz

explain:
	$(PY) -m auditforge.cli explain --seed 4242 --config '{"interactions":["partial_fx","cutoff_fx"]}'
