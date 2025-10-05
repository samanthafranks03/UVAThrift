from django.test import TestCase

# Create your tests here.#THIS DUMMY TEST WAS CREATED BY INSTRUCTOR MARK SHERIFF
class DummyTestCase(TestCase):
    def setUp(self):
        x = 1
        y = 2
    
    def test_dummy_test_case(self):
        self.assertEqual(2, 2)
