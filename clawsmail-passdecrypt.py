#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright (C) 2013-2016 Colomban Wendling <ban@herbesfolles.org>
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
try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser


PASSCRYPT_KEY = b'passkey0'


def pass_decrypt(p, key=PASSCRYPT_KEY, mode=DES.MODE_CFB):
    """ Decrypts a password from ClawsMail. """
    if p[0] == '!':  # encrypted password
        buf = b64decode(p[1:])

        """
        If mode is ECB or CBC and the length of the data is wrong, do nothing
        as would the libc algorithms (as they fail early).  Yes, this means the
        password wasn't actually encrypted but only base64-ed.
        """
        if (mode in (DES.MODE_ECB, DES.MODE_CBC)) and ((len(buf) % 8) != 0 or
                                                       len(buf) > 8192):
            d = buf
        else:
            c = DES.new(key, mode=mode, IV=b'\0'*8)
            d = c.decrypt(buf)

        try:
            return d.decode()
        except UnicodeDecodeError:
            return d
    else:  # raw password
        return p


def accountrc_decrypt(filename, key=PASSCRYPT_KEY, mode=DES.MODE_CFB):
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

            password = pass_decrypt(p.get(s, 'password'), key, mode=mode)
            print('password for %s, %s is "%s"' % (account, address, password))
        except Exception as e:
            print('Error resolving password for account "%s": %s' % (s, e))


if __name__ == '__main__':
    import os
    from optparse import OptionParser, OptionValueError

    def mode_callback(option, opt, value, parser):
        try:
            parser.values.mode = getattr(DES, 'MODE_'+value.upper())
        except AttributeError:
            raise OptionValueError('Invalid mode "%s"' % value)

    usage = 'Usage: %prog [OPTIONS] ENCRYPTED_PASS1...|FILE...'
    parser = OptionParser(usage=usage)
    parser.add_option('-k', '--key', dest='key', default=PASSCRYPT_KEY,
                      help='Use KEY to decode passwords (8 byte string) '
                           '[%default]',
                      metavar='KEY')
    parser.add_option('-m', '--mode', dest='mode', default=DES.MODE_CFB,
                      type='string', action='callback', callback=mode_callback,
                      help='Use MODE to decrypt DES passwords.  Choose ECB to '
                           'decrypt passwords from FreeBSD installations, CFB '
                           'otherwise [CFB]',
                      metavar='MODE')
    parser.add_option('--freebsd', dest='mode',
                      action='store_const', const=DES.MODE_ECB,
                      help='Use ECB mode as needed for passwords from FreeBSD '
                           '(alias for --mode=ECB)')
    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.error('missing file or string to decrypt')
    else:
        for a in args:
            if os.path.exists(a):
                accountrc_decrypt(a, key=options.key, mode=options.mode)
            else:
                password = pass_decrypt(a, key=options.key, mode=options.mode)
                print('password "%s" is "%s"' % (a, password))
