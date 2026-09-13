import unittest
from backend.risk_engine import calculate_risk

class RiskEngineTests(unittest.TestCase):
    def test_emergency_red_flag_is_high(self):
        r=calculate_risk({'mainProblem':'severe chest pain','severity':9,'duration':'Today','symptoms':['Chest pain']})
        self.assertEqual(r['level'],'High')
        self.assertGreaterEqual(r['score'],10)
    def test_mild_short_symptom_is_low_or_moderate(self):
        r=calculate_risk({'mainProblem':'mild headache','severity':2,'duration':'Less than 24 hours','symptoms':['Headache']})
        self.assertIn(r['level'],{'Low','Moderate'})

if __name__=='__main__':unittest.main()
