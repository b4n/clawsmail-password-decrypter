ClawsMail account password decryption
=====================================

If you ever need to "recover" a mailbox account password ClawsMail stored but
that you (or probably rather the user) don't remember, you'll quickly discover
they are stored in `~/.claws-mail/accountrc`.  However, you'll also see that
they aren't stored in plain text -- and that's the least they could do, you
probably wouldn't know your password stored without any kind of protection on
your hard drive.

How to decrypt this password?  At first it kinda look like Base64 (for those
who know about it) with a strange `!` ahead.  That's right, what you see is
Base64.  But you'll quickly see it isn't that naive if you try to decrypt it.

At this point, you'll probably either give up (if you can afford it), or do
what I did: read ClawsMail's sources.  Fortunately it's open source (well, this
probably was part of the reasons why you chose this client after all), so you
can get it and read it -- but I hope you read C.  You'll then dig a little in
the source, and finally find the interesting file: `passcrypt.c`.  This is
where the magic happens after the Base64: DES-CFB (or DES-ECB on FreeBSD,
you'll have to ask the author why there is a separate code path here...).

Maybe at this point you'll attempt to use the `openssl` command-line utility --
indeed, it looks promising --, and I wish you luck.  However I didn't succeed
at it, first guessing I didn't really knew what encryption was used -- but now
I really think I know what ClawsMail uses I'm thinking I either just have no
idea how to use this tool, or it's a bit broken.  Anyway, then, you'd probably
end up writing a tiny C program using the ClawsMail routine to perform the
decryption like I did.

To save you some time and headache browsing unknown code with a user crying,
I'm releasing the little tool I wrote.  I first wrote it in C because I know C
and ClawsMail is written in C so I could reuse their routine without caring
further about what it actually does, but re-did it in Python when thinking
about releasing it because I guess it'll be easier to use for you.


Python tool
-----------

`clawsmail-passdecrypt.py` is the Python (2.x) version of the tool (requires
`python-crypto`).  It can either decrypt arbitrary passwords, or parse a
ClawsMail `accountrc` file and extract the address/password information from
each account in it.

The usage is very simple, use either::

    python clawsmail-passdecrypt.py ~/.claws-mail/accountrc

or::

    python clawsmail-passdecrypt.py 'encryptedpassword'

This will give you something like this::

    $ python clawsmail-passdecrypt.py ~/.claws-mail/accountrc
    password for john@doe.co.uk is "mysecretpassword"
    password for john.doe@example.com is "thisissecret"

Note that DES requires a key.  By default ClawsMail uses `passkey0` as the key,
but this can be changed at build time.  The tool uses this as the default, but
supports the `-k <key>` switch if you need to use another one.

To decrypt passwords from a FreeBSD installation, use the `--freebsd` option,
which is an alias of the `--mode=ECB` option.


C tool
------

The C tool works pretty much like the Python tool, but you need to build it.
For this, you need a C compiler (like `GCC` or `CLang`), the GLib development
files, and most importantly ClawsMail's source code (actually its `passcrypt.c`
and `passcrypt.h` files). I suggest you to use the tool from your distribution
to fetch the source code of a package rather than manually downloading the
ClawsMail source code, because the `passcrypt.h` file is partially generated
and contains the DES key to use, so you should use the version of it that was
used to build the ClawsMail executable you actually use.  Under Debian and
derivates, it'll be ``apt-get source claws-mail``.  You also need `make` if you
want to use the Makefile (otherwise check the source code, there is a little
comment on how to build).

To build the thing, use::

    make CLAWSMAIL_SRC=/path/to/claws-mail/src

If you have a `make`, a C compiler and correctly specified the path to
ClawsMail source code, this should succeed and generate you an executable
called `clawsmail-passdecrypt`.  You can use it the same as the Python tool --
but it doesn't support the `-k` switch, the key is builtin.

If you need to decrypt a password from a FreeBSD version of ClawsMail but you
don't build on FreeBSD, you need to define the `NEED_DES_ECB` C preprocessor
constant.  You can use::

    make CLAWSMAIL_SRC=/path/to/claws-mail/src CFLAGS='-DNEED_DES_ECB'


Note on encryption under FreeBSD (DES-ECB)
------------------------------------------

As mentioned above, for some reason ClawsMail encrypts passwords using DES-ECB
instead of DES-CFB under FreeBSD.

DES-ECB doesn't allow encrypted blocks of sizes not multiple of 8, and
ClawsMail doesn't introduce padding nor checks the encryption actually
succeeded.  This means that password encryption under FreeBSD will fail
silently if the password length (in bytes) is not multiple of 8, leading to the
encryption phase simply being a no-op, meaning the password will only be
transformed through Base64.  This sounds bad, but it's how it is.
