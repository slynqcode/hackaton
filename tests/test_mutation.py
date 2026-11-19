from auditforge.mutants import MUTANTS, run_mutation_suite


def test_every_grader_mutant_is_killed():
    r = run_mutation_suite()
    assert r["mutants"] >= 30
    assert r["survivors"] == [], r["survivors"]


def test_mutation_patches_are_restored():
    from auditforge import grader as G
    before = (G._currency_ok, G.INSPECTION_COST, G.match_findings)
    run_mutation_suite()
    assert (G._currency_ok, G.INSPECTION_COST, G.match_findings) == before
