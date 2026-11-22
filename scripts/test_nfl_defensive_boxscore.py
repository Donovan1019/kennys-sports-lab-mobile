#!/usr/bin/env python3
"""Regression tests for observed ESPN NFL boxscore position subtotals."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('defensive',Path(__file__).with_name('build_nfl_defensive_comparison.py'))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def sample(qb,other):
    overall={'passing_yards_allowed':qb+other,'pass_attempts_allowed':10}
    return {'Baltimore Ravens':{'overall':overall,'qb':{'passing_yards_allowed':qb,'pass_attempts_allowed':9},'rb':{},'wr':{},'te':{}}}

class BoxscoreValidation(unittest.TestCase):
    def test_negative_other_passer_is_valid(self):
        mod.validate_box(sample(210,-4))
    def test_positive_non_qb_passer_is_valid(self):
        mod.validate_box(sample(210,4))
    def test_impossible_unsigned_subtotal_is_rejected(self):
        data=sample(210,0)
        data['Baltimore Ravens']['qb']['pass_attempts_allowed']=11
        with self.assertRaisesRegex(ValueError,'exceeds overall'):
            mod.validate_box(data)
    def test_negative_team_passing_yards_can_be_valid(self):
        mod.validate_box(sample(-3,-2))
    def test_negative_pass_attempts_rejected(self):
        data=sample(210,0)
        data['Baltimore Ravens']['qb']['pass_attempts_allowed']=-1
        with self.assertRaisesRegex(ValueError,'Invalid'):
            mod.validate_box(data)

if __name__=='__main__':unittest.main()
