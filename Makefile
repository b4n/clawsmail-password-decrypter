#!/usr/bin/make -f

CLAWSMAIL_SRC  ?= /usr/src/claws-mail*/src

PROGRAM           = clawsmail-passdecrypt
PROGRAM_SOURCES   = clawsmail-passdecrypt.c
PROGRAM_PACKAGES  = glib-2.0
PROGRAM_CFLAGS    = -I$(CLAWSMAIL_SRC)/common
PROGRAM_LDFLAGS   = -lcrypt

#=============================================================================#

CC         ?= cc
PKG_CONFIG ?= pkg-config
RM         ?= rm -f

CFLAGS  ?= -O2 -g
LDFLAGS ?=

PROGRAM_CFLAGS  += $(shell $(PKG_CONFIG) --cflags $(PROGRAM_PACKAGES) 2>/dev/null)
PROGRAM_LDFLAGS += $(shell $(PKG_CONFIG) --libs $(PROGRAM_PACKAGES) 2>/dev/null)

OBJECTS  = $(PROGRAM_SOURCES:%.c=%.o)


.PHONY: all clean distclean

all: $(PROGRAM)

$(PROGRAM): $(OBJECTS)
	$(CC) -o $@ $^ $(PROGRAM_LDFLAGS) $(LDFLAGS)

%.o: %.c
	$(CC) -o $@ -c $< $(PROGRAM_CFLAGS) $(CFLAGS)

clean:
	$(RM) $(OBJECTS) $(PROGRAM)
distclean: clean
