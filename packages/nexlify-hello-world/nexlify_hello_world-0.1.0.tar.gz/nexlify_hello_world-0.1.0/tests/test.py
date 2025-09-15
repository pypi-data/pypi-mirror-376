import unittest
from hello_world.test import saludar

class TestSaludar(unittest.TestCase):
    def test_saludar(self):
        self.assertEqual(saludar("Mundo"), "¡Hola, Mundo!")

if __name__ == "__main__":
    unittest.main()