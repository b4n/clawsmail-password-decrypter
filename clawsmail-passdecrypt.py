#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright (C) 2013 Colomban Wendling <ban@herbesfolles.org>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the following disclaimer
#   in the documentation and/or other materials provided with the
#   distribution.
# * Neither the name of the author nor the names of its contributors may
#   be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from Crypto.Cipher import DES
from base64 import standard_b64decode as b64decode
from ConfigParser import ConfigParser


PASSCRYPT_KEY = b'passkey0'


def pass_decrypt(p, key=PASSCRYPT_KEY):
    """
    Decrypts a password from ClawsMail.  This doesn't work for password stored
    under FreeBSD because then ClawsMail uses DES ECB mode, but apparently
    feeds it data of non-modulo 8 size.  This looks impossible, but apparently
    it works.  I checked the implementation of ecb_crypt() from the glibc, and
    it seems to actually not accept length non-modulo 8, although the ClawsMail
    code DOES work with it:

        des_setparity(des_key);
        ecb_crypt(des_key, password, len, DES_ENCRYPT);

    even when then length is clearly non-modulo 8.  I have no idea hot to deal
    with this then, so this won't work for FreeBSD users -- sorry guys.  They
    will either have to use a C implementation or find how to decrypt this.
    """
    if p[0] == '!':  # encrypted password
        c = DES.new(key, mode=DES.MODE_CFB, IV=b'\0'*8)
        return c.decrypt(b64decode(p[1:]))
    else:  # raw password
        return p


def accountrc_decrypt(filename, key=PASSCRYPT_KEY):
    """ Reads passwords from ClawsMail's accountrc file """
    p = ConfigParser()
    p.read(filename)

    for s in p.sections():
        try:
            try:
                address = p.get(s, 'address')
                account = p.get(s, 'account_name')
            except:
                address = '<unknown>'
                account = '<unknown>'

            password = pass_decrypt(p.get(s, 'password'), key)
            print('password for %s, %s is "%s"' % (account, address, password))
        except Exception as e:
            print('Error resolving password for account "%s": %s' % (s, e))


if __name__ == '__main__':
    import os
    from optparse import OptionParser

    usage = 'Usage: %prog [OPTIONS] ENCRYPTED_PASS1...|FILE...'
    parser = OptionParser(usage=usage)
    parser.add_option('-k', '--key', dest='key', default=PASSCRYPT_KEY,
                      help='Use KEY to decode passwords (8 byte string) '
                           '[%default]',
                      metavar='KEY')
    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.error('missing file or string to decrypt')
    else:
        for a in args:
            if os.path.exists(a):
                accountrc_decrypt(a, key=options.key)
            else:
                password = pass_decrypt(a, key=options.key)
                print('password "%s" is "%s"' % (a, password))
