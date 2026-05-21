# -*- coding: utf-8 -*-
"""
OpenPMU - Phasor XML
Copyright (C) 2022  www.OpenPMU.org

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

""" Convert phasor result between XML and python dictionary.

.. code :: python

    {
        Frame:int,
        Channels:int,
        Date:str,
        Time:str with microsecond,
        Channel_0:
        {
            Name:str,
            Type:str,
            Phase:str,
            Range:str,
            Freq: float,
            Angle: float,
            Mag: float,
            ROCOF:float,
        },
        Channel_1:{...},
        .,
        .,
        .,
    }

see :ref:`xml-exchange-format`
"""

from lxml import etree
import os

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
__author__ = 'Xiaodong'

# convert from xml to dict
# if no conversion needed, delete it from the expression
xmlTypeConvert = lambda tag: {'Frame': int,
                              'Channels': int,
                              'Freq': float,
                              'Angle': float,
                              'ROCOF': float,
                              'Mag': float,
                              }.get(tag, lambda x: x)

# convert from dict to xml value
# if no conversion needed, delete it from the expression
dictTypeConvert = lambda key: {'Frame': str,
                               'Channels': str,
                               'Angle': str,
                               'Freq': str,
                               'ROCOF': str,
                               'Mag': str,
                               }.get(key, lambda x: x)


def fromXML(xml):
    """
    Convert an xml string to a python dictionary.
    The python dict is mapped using the same structure of xml.

    :param xml: input xml string
    :return: python dict
    """

    phasorDict = dict()
    # parse the received data and store it in a dict
    level0 = etree.fromstring(xml)
    try:
        for level1 in list(level0):
            text = level1.text
            tag = level1.tag
            if tag.startswith("Channel_"):
                phasorDict[tag] = dict()
                for level2 in list(level1):
                    phasorDict[tag][level2.tag] = xmlTypeConvert(level2.tag)(level2.text)
            else:
                phasorDict[tag] = xmlTypeConvert(tag)(text)

    except AttributeError as e:
        print("Error occurred while parsing xml information")
        print(e)
        return None
    else:
        return phasorDict


# convert from python dictionary to a XML string
template = etree.parse(os.path.join(SCRIPT_DIRECTORY, "phasor.xml"))


def toXML(resultDict):
    """
    Convert a python dictionary to an xml string
    The python dict is mapped using the same structure of xml.

    :param resultDict: python dictionary
    :return: xml string
    """

    level0 = template.getroot()

    try:
        for level1 in list(level0):
            tag1 = level1.tag
            if tag1 not in resultDict.keys():
                continue
            if tag1.startswith("Channel_"):
                for level2 in list(level1):
                    tag2 = level2.tag
                    level2.text = dictTypeConvert(tag2)(resultDict[tag1][tag2])
            else:
                level1.text = dictTypeConvert(tag1)(resultDict[tag1])
    except KeyError as e:
        print("XML tag error: ", e)
    xml = etree.tostring(level0, encoding="utf-8")
    return xml
