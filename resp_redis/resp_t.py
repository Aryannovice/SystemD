import unittest
from resp import decode
# Assume you have a function `decode(data: bytes)` implemented
# that handles RESP decoding (like core.Decode in Go).

class TestRESPDecode(unittest.TestCase):

    def test_simple_string(self):
        cases = {
            b"+OK\r\n": "OK",
        }
        for k, v in cases.items():
            value, _ = decode(k)
            self.assertEqual(v, value)

    def test_error(self):
        cases = {
            b"-Error message\r\n": "Error message",
        }
        for k, v in cases.items():
            value, _ = decode(k)
            self.assertEqual(v, value)

    def test_int64(self):
        cases = {
            b":0\r\n": 0,
            b":1000\r\n": 1000,
        }
        for k, v in cases.items():
            value, _ = decode(k)
            self.assertEqual(v, value)

    def test_bulk_string(self):
        cases = {
            b"$5\r\nhello\r\n": "hello",
            b"$0\r\n\r\n": "",
        }
        for k, v in cases.items():
            value, _ = decode(k)
            self.assertEqual(v, value)

    def test_array(self):
        cases = {
            b"*0\r\n": [],
            b"*2\r\n$5\r\nhello\r\n$5\r\nworld\r\n": ["hello", "world"],
            b"*3\r\n:1\r\n:2\r\n:3\r\n": [1, 2, 3],
            b"*5\r\n:1\r\n:2\r\n:3\r\n:4\r\n$5\r\nhello\r\n": [1, 2, 3, 4, "hello"],
            b"*2\r\n*3\r\n:1\r\n:2\r\n:3\r\n*2\r\n+Hello\r\n-World\r\n":
                [[1, 2, 3], ["Hello", "World"]],
        }
        for k, v in cases.items():
            value, _ = decode(k)
            self.assertEqual(len(value), len(v))
            for i in range(len(v)):
                self.assertEqual(str(v[i]), str(value[i]))


if __name__ == "__main__":
    unittest.main()
