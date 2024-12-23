#!/usr/bin/python3
# -*- coding: utf-8 -*-
# (k) made-on-the-knee-of /dragon

import unittest
import random
import string

from util import Cryptor

class TestCryptor(unittest.TestCase):

    def test_local_encode_decode(self):
        cr = Cryptor()
        cr.setapp(None)
        s1 = ''.join(random.choices(string.ascii_letters, k=4096))
        e1 = cr.encrypt(s1)
        s2 = cr.decrypt(e1).decode()
        self.assertEqual(s1, s2)

    def test_foreign_encode_decode(self):
        cr1 = Cryptor()
        cr1.setapp(None)
        cr2 = Cryptor()
        cr2.setapp(None)
        key = cr1.publickey()
        s1 = ''.join(random.choices(string.ascii_letters, k=4096))
        e1 = cr2.staticencrypt(key, s1)
        s2 = cr1.decrypt(e1).decode()
        self.assertEqual(s1, s2)

if __name__ == "__main__":
    unittest.main()
