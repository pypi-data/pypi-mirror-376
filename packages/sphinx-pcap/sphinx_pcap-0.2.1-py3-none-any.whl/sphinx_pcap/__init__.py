
#   Copyright 2024 CANCOM Austria AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import sys
import os
from docutils.parsers.rst import Directive, directives
from docutils import nodes



__version__=0.2

class PCAP(Directive):
    required_arguments = 0
    optional_arguments = 4
    has_content = False

    option_spec = {
        'linenos': directives.flag,
        'output_language': directives.unchanged,  # needed for pygments lexer on output data
        'filename': directives.path,
        'tshark_path': directives.path,
        'frames': directives.unchanged,
        'filter': directives.unchanged,

    }

    
    def get_frame_filter(self,filter_string):
        r = []
        for i in filter_string.split(','):
            if '-' not in i:
                r.append(int(i))
            else:
                l,h = map(int, i.split('-'))
                r+= range(l,h+1)
        retval="or ".join(r)
        return f"({retval})"


    
    def run(self):
        output_language = self.options.get('output_language') or 'none'
        filename = self.options.get('filename')
        tshark_path = self.options.get('tshark_path') or '/usr/bin/tshark'
        _frame_display_filter=""
        if self.options.get('frames'):
            _frame_display_filter=self.get_frame_filter()
        

        # display_filter = self.options.get('display_filter') or ''
        _cli=[tshark_path,'-r',filename,'-V',]



def setup(app):
    """ Register directive with Sphinx """
    app.add_directive('include_pcap', PCAP)
    return {'version': __version__}
