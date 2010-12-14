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

"""This script will parse a directory of blog comments found at ILPS:
http://ilps.science.uva.nl/resources/commentspam
The script should be run with the blog-spam-assessments in the same directory
as the blog folders.
Example usage:
$python spamparse.py
"""

__author__ = 'Robert Kaplow'

import re
import xml.dom.minidom

assessment_list = open('blog-spam-assessments.txt', 'r')

# output file
fixed = open('fixed.csv', 'w')


def GetText(nodelist):
  out = []
  for node in nodelist:
    if node.nodeType == node.TEXT_NODE:
      out.append(node.data)
  return ''.join(out)


for line in assessment_list:
  linelist = line.split()
  comment_file = linelist[0]
  comment_id = linelist[1]
  tag = linelist[2]

  if comment_file[0] is not '#':
    file_dom = xml.dom.minidom.parse(comment_file)
    label = 'error'
    if tag == '1':
      label = 'spam'
    elif tag == '0':
      label = 'ham'
    dom_comments = file_dom.getElementsByTagName(
        'blog-page')[0].getElementsByTagName('comment')
    for comment in dom_comments:
      if comment_id == comment.getAttribute('id'):
        comment_text = GetText(comment.childNodes)
        comment_text = re.sub('\"', '', comment_text)
        comment_text = re.sub('\n', '', comment_text)
        final_line = '\"' + label + '\", \"' + comment_text + '\"'
        fixed.write(final_line)
        fixed.write('\n')
        break
