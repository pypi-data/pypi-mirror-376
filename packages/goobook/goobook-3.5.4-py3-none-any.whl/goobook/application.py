#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: fileencoding=UTF-8 filetype=python ff=unix et ts=4 sw=4 sts=4 tw=120
# author: Christer Sjöholm -- hcs AT furuvik DOT net


import argparse
import datetime
import importlib.metadata
import locale
import logging
import pathlib
import json
import sys

from google_auth_oauthlib import flow

import goobook.config
from goobook.goobook import GooBook, Cache, GoogleContacts, parse_groups, parse_contacts
from goobook.storage import unstorageify

log = logging.getLogger(__name__)  # pylint: disable=invalid-name

SCOPES = 'https://www.googleapis.com/auth/contacts'  # read/write access to Contacts and Contact Groups

AUTHENTICATE_HELP_STRING = '''Google OAuth authentication.

Before running goobook authenticate you need a client secrets JSON file, get it like this:

Go to https://developers.google.com/people/quickstart/python
and click "Enable the People API"
select a name (ex. GooBook)
select desktop application
click "download JSON" to be used below

    $ goobook authenticate -- client_secrets.json

and follow the instructions.

If you get the page "This app isn't verified" select Advanced and the "Go to GooBook (unsafe)" at the bottom.
'''


def main():
    locale.setlocale(locale.LC_TIME, '')  # Use system configured locale

    parser = argparse.ArgumentParser(description='Search you Google contacts from mutt or the command-line.')
    parser.add_argument('-c', '--config', help='Specify alternative configuration file.', metavar="FILE")
    parser.add_argument('-v', '--verbose', dest="log_level", action='store_const',
                        const=logging.INFO, help='Be verbose about what is going on (stderr).')
    parser.add_argument('-V', '--version',
                        action='version',
                        version='%%(prog)s %s' % importlib.metadata.version("goobook"),
                        help="Print version and exit")
    parser.add_argument('-d', '--debug', dest="log_level", action='store_const',
                        const=logging.DEBUG, help='Output debug info (stderr).')
    parser.set_defaults(log_level=logging.ERROR)

    subparsers = parser.add_subparsers()

    parser_add = subparsers.add_parser('add',
                                       description='Create new contact, if name and email is not given the'
                                       ' sender of a mail read from stdin will be used.')
    parser_add.add_argument('name', nargs='?', metavar='NAME',
                            help='Name to use.')
    parser_add.add_argument('email', nargs='?', metavar='EMAIL',
                            help='E-mail to use.')
    parser_add.add_argument('phone', nargs='?', metavar='PHONE',
                            help='Phone number to use.')
    parser_add.set_defaults(func=do_add)

    parser_config_template = subparsers.add_parser('config-template',
                                                   description='Prints a template for .goobookrc to stdout')
    parser_config_template.set_defaults(func=do_config_template)

    parser_dump_contacts = subparsers.add_parser('dump_contacts',
                                                 description='Dump contacts as JSON.')
    parser_dump_contacts.add_argument('-p', '--parse', action='store_true', help='Dump parsed contact instead of raw.')
    parser_dump_contacts.set_defaults(func=do_dump_contacts)

    parser_dump_groups = subparsers.add_parser('dump_groups',
                                               description='Dump groups as JSON.')
    parser_dump_groups.add_argument('-p', '--parse', action='store_true', help='Dump parsed contact instead of raw.')
    parser_dump_groups.set_defaults(func=do_dump_groups)

    parser_query = subparsers.add_parser('query',
                                         description='Search contacts using query (regex).')
    parser_query.add_argument('-s', '--simple', action='store_true',
                                    help='Simple output format instead of mutt compatible')
    parser_query.add_argument('query', help='regex to search for.', metavar='QUERY')
    parser_query.set_defaults(func=do_query)

    parser_query_details = subparsers.add_parser(
        'dquery',
        description='Search contacts using query (regex) and print out all info.')
    parser_query_details.add_argument('query', help='regex to search for.')
    parser_query_details.set_defaults(func=do_query_details)

    parser_reload = subparsers.add_parser('reload',
                                          description='Force reload of the cache.')
    parser_reload.set_defaults(func=do_reload)

    parser_auth = subparsers.add_parser('authenticate',
                                        description=AUTHENTICATE_HELP_STRING,
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_auth.add_argument('client_secrets_json', metavar='CLIENT_SECRETS_JSON',
                             help='Client secrets JSON file')
    parser_auth.set_defaults(func=do_authenticate)

    parser_unauth = subparsers.add_parser('unauthenticate',
                                          description="Removed authentication data (logout).")
    parser_unauth.set_defaults(func=do_unauthenticate)

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)

    if 'func' not in args:
        parser.error('To few arguments.')

    try:
        if args.func is do_config_template:
            config = None
        else:
            config = goobook.config.read_config(args.config)
        args.func(config, args)
    except goobook.config.ConfigError as err:
        sys.exit('Configuration error: ' + str(err))

    if config:
        goobook.config.maybe_save_creds(config)

##############################################################################
# sub commands


def do_add(config, args):
    goobk = GooBook(config)
    if args.name and args.email:
        goobk.add_mail_contact(args.name, args.email, args.phone)
    else:
        goobk.add_email_from(sys.stdin)
    goobk.cache.load(force_update=True)


def do_config_template(_config, _args):
    print(goobook.config.TEMPLATE)


def do_dump_contacts(config, args):
    goco = GoogleContacts(config)
    contacts = goco.fetch_contacts()
    if args.parse:
        groupname_by_id = parse_groups(goco.fetch_contact_groups())
        contacts = unstorageify(list(parse_contacts(goco.fetch_contacts(), groupname_by_id)))

    class DateEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime.date):
                return str(obj)
            # Let the base class default method raise the TypeError
            return json.JSONEncoder.default(self, obj)
    print(json.dumps(contacts, sort_keys=True, indent=4, ensure_ascii=False, cls=DateEncoder))


def do_dump_groups(config, args):
    goco = GoogleContacts(config)
    groups = goco.fetch_contact_groups()
    if args.parse:
        groupname_by_id = parse_groups(goco.fetch_contact_groups())
        groups = unstorageify(list(groupname_by_id.values()))

    print(json.dumps(groups, sort_keys=True, indent=4, ensure_ascii=False))


def do_query(config, args):
    goobk = GooBook(config)
    goobk.query(args.query, simple=args.simple)


def do_query_details(config, args):
    goobk = GooBook(config)
    goobk.query_details(args.query)


def do_reload(config, _args):
    cache = Cache(config)
    cache.load(force_update=True)


def do_authenticate(config, args):
    creds = config.creds

    if not creds:
        f = flow.InstalledAppFlow.from_client_secrets_file(args.client_secrets_json, SCOPES)
        config.creds = f.run_local_server()
    else:
        print('You are already authenticated.')


def do_unauthenticate(config, _args):
    oauth_db = pathlib.Path(config.oauth_db_filename)
    if oauth_db.exists():
        oauth_db.unlink()
        print("deleted", oauth_db)
    config.creds = None


if __name__ == '__main__':
    main()
