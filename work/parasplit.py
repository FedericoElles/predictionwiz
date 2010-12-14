#!/usr/bin/env python
#
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This script will take as input a text file and a label, and will return a
CSV format file where each line in the file is a paragraph in the original
text, and the label for each line is the label in the input file. Here we
define a paragraph as anything split between two newlines.
Sample usage:
$python parasplit.py valid_posts ham
"""

__author__ = 'Robert Kaplow'

import re
import sys
fread = open(sys.argv[1], 'r')
outfile = sys.argv[1] + '.csv'
fwrite = open(outfile, 'w')
fullstring = fread.read().decode('ascii', 'ignore')
label = sys.argv[2]

splitfile = re.split('\n\n+', fullstring)
for line in splitfile:
  line = re.sub('\n', '', line)  #Remove all extra newlines.
  line = re.sub('\"', '', line)  #Remove all extra quotes.
  line = line.strip()
  if len(line) > 1:
    print line
    line = '\"' + label + '\", \"' + line + '\"'
    fwrite.write(line)
    fwrite.write('\n')

print 'Number of paragraphs found: ' + str(len(splitfile))
