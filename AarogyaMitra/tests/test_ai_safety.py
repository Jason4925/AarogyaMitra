import unittest
from backend.ai_safety import validate_response

class SafetyTests(unittest.TestCase):
    def test_dosage_is_blocked(self):
        r=validate_response('Take 500 mg twice daily.')
        self.assertFalse(r['passed'])
        self.assertIn('medication_dosage',r['issues'])
    def test_safe_response_passes(self):
        r=validate_response('This can have several causes. A clinician can assess persistent symptoms.')
        self.assertTrue(r['passed'])

if __name__=='__main__':unittest.main()
