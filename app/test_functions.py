import unittest
from app.functions import *

class FunctionTestCase(unittest.TestCase):
    def test_mariadb_name(self):
        self.assertRaises(TypeError, mariadb_name, "mar-i-a","---db")
        self.assertEqual(
            mariadb_name(
                "c303282d-f2e6-46ca-a04a-35d3d873712d",
                "c303282d-f2e6-46ca-a04a-35d3d873712f"
            ),
            'c303282df2e646caa04a35d3d873712dc303282df2e646caa04a35d3d873712f'
        )
    def test_is_uuid_like(self):
        self.assertFalse(is_uuid_like(None))
        self.assertFalse(is_uuid_like(""))
        self.assertFalse(is_uuid_like("sfdfdsfdsfsf"))
        self.assertTrue(is_uuid_like(uuid.UUID(int=0).hex))
        self.assertTrue(is_uuid_like(uuid.uuid4().hex))

if __name__ == '__main__':
    unittest.main()
