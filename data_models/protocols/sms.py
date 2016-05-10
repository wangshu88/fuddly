################################################################################
#
#  Copyright 2014-2016 Eric Lacombe <eric.lacombe@security-labs.org>
#
################################################################################
#
#  This file is part of fuddly.
#
#  fuddly is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  fuddly is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with fuddly. If not, see <http://www.gnu.org/licenses/>
#
################################################################################import sys

from fuzzfmk.data_model import *
from fuzzfmk.value_types import *
from fuzzfmk.data_model_helpers import *

class SMS_DataModel(DataModel):

    file_extension = 'sms'

    def absorb(self, data, idx):
        pass

    def build_data_model(self):

        # Text SMS in PDU mode
        smstxt_desc = \
        {'name': 'smstxt',
         'contents': [
             {'name': 'TP-DA',  # Destination Address
              'semantics': ['tel num'],
              'contents': GSMPhoneNum(val_list=['33612345678'])},
             {'name': 'TP-PID',  # Protocol Identifier (refer to TS 100 901)
              'determinist': True,
              'contents': BitField(subfield_sizes=[5,1,2], endian=VT.BigEndian,
                                   subfield_val_lists=[[0b00000], # implicit
                                                       [0, 1],       # no interworking (default)
                                                       [0b00, 0b01, 0b11]]  # 0b10 is reserved
                                   ) },
             {'name': 'TP-DCS',  # Data Coding Scheme (refer to GSM 03.38)
              'determinist': True,
              'contents': BitField(subfield_sizes=[4,4], endian=VT.BigEndian,
                                   subfield_val_lists=[[0b0000],   # default alphabet
                                                       [0b0000]]   # first coding group
                                   ) },
             {'name': 'UDL',
              'contents': MH.LEN(vt=UINT8, after_encoding=False),
              'node_args': 'user_data'},
             {'name': 'user_data',
              'contents': GSM7bitPacking(val_list=['Hello World!'], max_sz=160)
             }
         ]
        }

        # SIM Toolkit commands
        smscmd_desc = \
        {'name': 'smscmd',   # refer to GSM 03.48
         'contents': [
             {'name': 'TP-DA',  # Destination Address
              'semantics': ['tel num'],
              'contents': GSMPhoneNum(val_list=['33612345678'])},
             {'name': 'TP-PID',  # Protocol Identifier (refer to TS 100 901)
              'determinist': True,
              'contents': BitField(subfield_sizes=[5,1,2], endian=VT.BigEndian,
                                   subfield_val_lists=[[0b11111], # GSM mobile station
                                                       [1, 0],    # telematic interworking (default)
                                                       [0b01, 0b00, 0b11]],
                                   ) },
             {'name': 'TP-DCS',  # Data Coding Scheme (refer to GSM 03.38)
              'determinist': True,
              'contents': BitField(subfield_sizes=[2,1,1,4], endian=VT.BigEndian,
                                   subfield_val_lists=[[0b10,0b11,0b00,0b01], # class 2 (default)
                                                       [1,0],    # 8-bit data (default)
                                                       [0],      # reserved
                                                       [0b1111]],  # last coding group
                                   ) },
             {'name': 'UDL',
              'contents': MH.LEN(vt=UINT8),
              'node_args': 'user_data'},
             {'name': 'user_data',
              'contents': [
                  {'name': 'UDHL',
                   'contents': UINT8(int_list=[2])},
                  {'name': 'IEIa', # 0x70 = command packet identifier
                   'contents': UINT8(int_list=[0x70], mini=0x70, maxi=0x7F)},
                  {'name': 'IEDLa',
                   'contents': UINT8(int_list=[0])},
                  {'name': 'CPL',  # command packet length
                   'contents': MH.LEN(vt=UINT16_be),
                   'node_args': 'cmd'},
                  {'name': 'cmd',
                   'contents': [
                       {'name': 'CHL', # command header length
                        'contents': MH.LEN(vt=UINT8),
                        'node_args': 'cmd_hdr'},
                       {'name': 'cmd_hdr',
                        'contents': [
                            {'name': 'SPI_p1',  # Security Parameter Indicator (part 1)
                             'contents': BitField(subfield_sizes=[2,1,2,3], endian=VT.BigEndian,
                                                  subfield_val_lists=[[1], # redundancy check
                                                                      [0], # no ciphering
                                                                      [0], # no counter
                                                                      [0b000]],
                                                  subfield_val_extremums=[[0,3],[0,1],[0,3],None],
                                                  subfield_descs=['chksum', 'ciph', 'count', 'reserved']
                                                  ) },

                            {'name': 'SPI_p2',  # Security Parameter Indicator (part 1)
                             'contents': BitField(subfield_sizes=[2,2,1,1,2], endian=VT.BigEndian,
                                                  subfield_val_lists=[[1], # PoR required
                                                                      [3], # PoR Digital Signature required
                                                                      [0], # PoR not ciphered
                                                                      [1], # PoR through SMS-SUBMIT
                                                                      [0b00]],
                                                  subfield_val_extremums=[[0,2],[0,3],[0,1],[0,1],None],
                                                  subfield_descs=['PoR', 'PoR chk', 'PoR ciph',
                                                                  'delivery', 'reserved']
                                                  ) },

                            {'name': 'KIc',  # Key and algo ID for ciphering
                             'contents': BitField(subfield_sizes=[2,2,4], endian=VT.BigEndian,
                                                  subfield_val_lists=[[1,0,3], # 1 = DES (default)
                                                                      [3],     # ECB mode
                                                                      [0b1010]],
                                                  subfield_val_extremums=[None,[0,3],None],
                                                  subfield_descs=['ciph algo', 'ciph mode', 'key indic']
                                                  ) },

                            {'name': 'KID',  # Key and algo ID for RC/CC/DS
                             'contents': BitField(subfield_sizes=[2,2,4], endian=VT.BigEndian,
                                                  subfield_val_lists=[[1,0,3], # 1 = DES (default)
                                                                      [0],     # CBC mode
                                                                      [0b1010]],
                                                  subfield_val_extremums=[None,[0,2],None],
                                                  subfield_descs=['ciph algo', 'ciph mode', 'key indic']
                                                  ) },

                            {'name': 'TAR',  # Toolkit Application Reference
                             'contents': BitField(subfield_sizes=[24],
                                                  subfield_val_lists=[[0]], # Card Manager
                                                  subfield_val_extremums=[[0,2**24-1]])},

                            {'name': 'CNTR',  # Counter (replay detection and sequence integrity counter)
                             'contents':  BitField(subfield_sizes=[40],
                                                   subfield_val_extremums=[[0,2**40-1]]) },

                            {'name': 'PCNTR',  # padding counter
                             'contents': UINT8() },

                            {'name': 'RC|CC|DS',  # redundancy check, crypto check, or digital sig
                             'exists_if': (BitFieldCondition(sf=0,val=1), 'SPI_p1'),  # RC only
                             'contents': MH.CRC(vt=UINT32_be),  # TODO: update checksum algo
                             'node_args': ['SPI_p1','SPI_p2','KIc','KID','TAR','CNTR','PCNTR','SecData']},

                            {'name': 'SecData',
                             'contents': String(min_sz=1, max_sz=100, determinist=False)}
                        ]},

                   ]},

              ]}
         ]}


        self.register(smstxt_desc, smscmd_desc)

data_model = SMS_DataModel()
