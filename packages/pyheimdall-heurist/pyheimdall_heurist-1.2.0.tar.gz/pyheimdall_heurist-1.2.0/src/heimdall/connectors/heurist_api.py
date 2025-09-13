# -*- coding: utf-8 -*-
import requests
import heimdall
from heimdall.connectors.heurist_xml import Builder
from heimdall.decorators import get_database
from heimdall.elements import Root, Item, Metadata
from xml.etree import ElementTree as etree
from xml.etree.ElementTree import Element
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen

"""
Provides connectors to Heurist-formatted XML files (HML).

This module defines an input connector to databases composed in full or in part of such XML files.

:copyright: The pyHeimdall contributors.
:licence: Afero GPL, see LICENSE for more details.
:SPDX-License-Identifier: AGPL-3.0-or-later
"""  # nopep8: E501


@get_database('heurist:api')
def getDatabase(**options):
    r"""Imports a database from a Heurist server

    :param \**options: Keyword arguments, see below.
    :Keyword arguments:
        * **dbname** (:py:class:`str`) -- Database name
        * **url** (:py:class:`str`, optional, default: ``https://heurist.huma-num.fr/heurist``) -- Heurist server URL
        * **format** (:py:class:`str`, optional) Always ``heurist:api``
    :return: HERA element tree
    :rtype: :py:class:`xml.etree.ElementTree.Element`

    Usage example: ::

      >>> import heimdall
      >>> tree = heimdall.getDatabase(format='heurist:xml', url='some/input.xml')
      >>> # ... do stuff ...

    .. CAUTION::
       For future compability, this function shouldn't be directly called; as shown in the usage example above, it should only be used through :py:class:`heimdall.getDatabase`.
    """  # nopep8: E501
    url = options['url']
    o = urlparse(url)
    db = parse_qs(o.query)['db'][0]
    baseurl = o._replace(query='').geturl()
    if baseurl.endswith('/'):
        baseurl = baseurl[:-1]
    username = options.get('username', None)
    password = options.get('password', None)

    with connect(db, username, password, baseurl=baseurl) as session:
        # get records
        url = f'{session.baseurl}/export/xml/flathml.php?db={db}&q=sortby%3A-m'
        response = session.get(url, timeout=session.timeout)
        if response.status_code != requests.codes.OK:
            message = response.json()['message']
            raise requests.exceptions.RequestException(message)
        content_records = response.content.decode('utf-8')
        # get structure
        if options.get('update', True):
            url = f'{session.baseurl}/hserv/structure/export/getDBStructureAsXML.php?db={db}&q=sortby%3A-m'  # nopep8: E501
            response = session.get(url, timeout=session.timeout)
            if response.status_code != requests.codes.OK:
                message = response.json()['message']
                raise requests.exceptions.RequestException(message)
            content_structure = response.content.decode('utf-8')

    structure = etree.ElementTree(etree.fromstring(content_structure))
    record_types = _get_record_types(structure)
    detail_types = _get_detail_types(structure)
    displays = _get_display_fields(structure)

    target = Builder()
    parser = etree.XMLParser(target=target)
    tree = etree.fromstring(content_records, parser)
    if options.get('update', True):
        heimdall.util.update_entities(tree)

        def by_id(node):
            return node.attrib['id'] == id_

        for eid, name in target.entity_names.items():
            id_ = eid
            e = heimdall.getEntity(tree, by_id)
            info = record_types.get(eid, None)
            e.name = info['name']
            e.description = info['description']

            for aid, name in target.attribute_names.items():
                id_ = aid
                a = heimdall.getAttribute(e, by_id)
                if a is not None:
                    parts = aid.split('.')
                    assert len(parts) == 2 and parts[0] == eid
                    pid = parts[-1]
                    base_info = detail_types[pid]
                    display_info = _get_display_field(
                            displays,
                            info['hid'],
                            base_info['hid']
                            )
                    if display_info is not None:
                        a.name = display_info['name']
                        a.description = display_info['description']
                    targets_hid = base_info['targets']
                    if targets_hid is not None:
                        targets = list()
                        for hid in targets_hid:
                            target_eid = _get_eid(record_types, hid)
                            targets.append(f'{target_eid}.id')
                        targets = ','.join(targets)
                        a.type = f'@{targets}'

        for pid, name in target.property_names.items():
            id_ = pid
            p = heimdall.getProperty(tree, by_id)
            info = detail_types.get(pid, None)
            p.name = info['name']
            p.description = info['description']

    return tree


def _get_conceptID(e, ns):
    prefix = str(int(e.find(f'./{ns}_OriginatingDBID').text))
    suffix = str(int(e.find(f'./{ns}_IDInOriginatingDB').text))
    eid = f'{prefix}-{suffix}'
    return eid


def _get_record_types(structure):
    results = dict()
    NS = 'rty'
    elements = structure.findall('./RecTypes')[0].findall(f'./{NS}')
    for e in elements:
        eid = _get_conceptID(e, NS)
        hid = e.find(f'./{NS}_ID').text
        name = e.find(f'./{NS}_Name').text
        description = e.find(f'./{NS}_Description').text
        results[eid] = {
                'hid': hid,
                'name': name, 'description': description,
                }
    return results


def _get_detail_types(structure):
    results = dict()
    NS = 'dty'
    elements = structure.findall('./DetailTypes')[0].findall(f'./{NS}')
    for e in elements:
        eid = _get_conceptID(e, NS)
        hid = e.find(f'./{NS}_ID').text
        name = e.find(f'./{NS}_Name').text
        description = e.find(f'./{NS}_HelpText').text
        targets = e.find(f'./{NS}_PtrTargetRectypeIDs').text
        if targets is not None:
            targets = targets.split(',')
        results[eid] = {
                'hid': hid,
                'name': name, 'description': description,
                'targets': targets,
                }
    return results


def _get_display_fields(structure):
    results = dict()
    NS = 'rst'
    elements = structure.findall('./RecStructure')[0].findall(f'./{NS}')
    for e in elements:
        hid = e.find(f'./{NS}_ID').text
        record_type_hid = e.find(f'./{NS}_RecTypeID').text
        detail_type_hid = e.find(f'./{NS}_DetailTypeID').text
        name = e.find(f'./{NS}_DisplayName').text
        description = e.find(f'./{NS}_DisplayHelpText').text
        results[hid] = {
                'record_type_hid': record_type_hid,
                'detail_type_hid': detail_type_hid,
                'name': name, 'description': description,
                }
    return results


def _get_display_field(displays, record_type_hid, detail_type_hid):
    for hid, info in displays.items():
        if (info['record_type_hid'] == record_type_hid and
           info['detail_type_hid'] == detail_type_hid):
            return info
    return None


def _get_eid(results, hid):
    for eid, data in results.items():
        if data['hid'] == hid:
            return eid
    return None


class connect:
    def __init__(self,
                 dbname, username, password,
                 baseurl='https://heurist.huma-num.fr/heurist',
                 timeout=10,
                 ):
        self.session = requests.Session()
        self.session.baseurl = baseurl
        self.session.dbname = dbname
        self.session.timeout = timeout
        self.__username = username
        self.__password = password
        self.url = f'{baseurl}/api/login'

    def __enter__(self):
        response = self.session.post(
                url=self.url,
                data={
                    'db': self.session.dbname,
                    'login': self.__username,
                    'password': self.__password,
                    },
                timeout=self.session.timeout,
                )
        if response.status_code != requests.codes.OK:
            message = response.json()['message']
            raise requests.exceptions.ConnectionError(message)

        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        self.__username = None
        self.__password = None


__copyright__ = "Copyright the pyHeimdall contributors."
__license__ = 'AGPL-3.0-or-later'
__version__ = '1.1.0'
__all__ = ['getDatabase', '__version__']
