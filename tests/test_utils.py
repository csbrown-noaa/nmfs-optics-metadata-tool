import unittest
import utils

class TestSomething(unittest.TestCase):

    def test_something(self):
        self.assertEqual(1,1)

def load_tests(loader, tests, ignore):
    return utils.doctests(pycocowriter.utils, tests)

if __name__ == '__main__':
    unittest.main()
