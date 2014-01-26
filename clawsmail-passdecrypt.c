/*
 * Copyright (C) 2012-2013 Colomban Wendling <ban@herbesfolles.org>
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 *
 * * Redistributions of source code must retain the above copyright
 *   notice, this list of conditions and the following disclaimer.
 * * Redistributions in binary form must reproduce the above
 *   copyright notice, this list of conditions and the following disclaimer
 *   in the documentation and/or other materials provided with the
 *   distribution.
 * * Neither the name of the author nor the names of its contributors may
 *   be used to endorse or promote products derived from this software
 *   without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/* build with:
gcc -o clawsmail-passdecrypt clawsmail-passdecrypt.c \
    -I/path/to/clawsmail/src/common \
    `pkg-config --cflags --libs glib-2.0` \
    -lcrypt
*/

#ifndef USE_CLAWSMAIL_SRC
/* we need to build our own version if we want the ECB decryption and not
 * building under FreeBSD -- see clawsmail's sources */
# define USE_CLAWSMAIL_SRC (defined(__FreeBSD__) || !defined(NEED_DES_ECB))
#endif


/* passcrypt from claws-mail -- needs to come before our includes */
#if USE_CLAWSMAIL_SRC
#	include "passcrypt.c"
#endif


#include <string.h>
#include <stdio.h>
#include <glib.h>


#if !USE_CLAWSMAIL_SRC
#	include <rpc/des_crypt.h>
#	define PASSCRYPT_KEY "passkey0"
/* taken from ClawsMail passcrypt.c */
static void passcrypt_decrypt(gchar *password, guint len)
{
	char des_key[8] = PASSCRYPT_KEY;

	des_setparity(des_key);
	ecb_crypt(des_key, password, len, DES_DECRYPT);
}
#endif /* !USE_CLAWSMAIL_SRC */


static gchar *pass_decrypt(const gchar *input)
{
	gchar *output;

	if (input[0] == '!') {
		gsize len;
		gchar *dec;

		dec = (gchar *) g_base64_decode(&input[1], &len);
		passcrypt_decrypt(dec, (guint) len);
		output = dec;
	} else {
		output = g_strdup(input);
	}

	return output;
}

static void accountrc_decrypt(const gchar *filename)
{
	GKeyFile *kf = g_key_file_new();
	GError *error = NULL;

	if (! g_key_file_load_from_file(kf, filename, 0, &error)) {
		fprintf(stderr, "Failed to open file: %s\n", error->message);
		g_error_free(error);
	} else {
		gsize n_groups, i;
		gchar **groups = g_key_file_get_groups(kf, &n_groups);

		for (i = 0; i < n_groups; i++) {
			gchar *input = g_key_file_get_value(kf, groups[i], "password", NULL);
			gchar *address = g_key_file_get_value(kf, groups[i], "address", NULL);
			gchar *account = g_key_file_get_value(kf, groups[i], "account_name", NULL);
			gchar *output = input ? pass_decrypt(input) : NULL;

			printf("password for %s, %s is \"%s\"\n", account, address, output);
			g_free(input);
			g_free(output);
			g_free(address);
			g_free(account);
		}
		g_strfreev(groups);
	}
	g_key_file_free(kf);
}

int main(int argc, char **argv)
{
	int i;

	if (argc < 2) {
		printf("Usage: %s [ENCRYPTED_PASS1...|FILE...]\n", argv[0]);
	}

	for (i = 1; i < argc; i++) {
		if (g_file_test(argv[i], G_FILE_TEST_EXISTS)) {
			/* file exists, let's guess it's a clawsmail accountrc */
			accountrc_decrypt(argv[i]);
		} else {
			gchar *pass = pass_decrypt(argv[i]);

			printf("password \"%s\" is \"%s\"\n", argv[i], pass);
			g_free(pass);
		}
	}

	return 0;
}
