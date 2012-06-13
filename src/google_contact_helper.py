#!/usr/bin/python
#
# https://developers.google.com/google-apps/contacts/v3/

import sys
import os
import getopt
import glob
import codecs
#import atom
#import gdata.contacts.data
import gdata.contacts.client

from xml.etree             import ElementTree
from xml.etree.ElementTree import Element, SubElement
from xml.dom               import minidom

class GoogleContacts(object):
  """GoogleContacts object provides helper methods to access Google contacts."""

  def __init__(self, user, pw):
    """Constructor for the GoogleContacts object."""
    # instanciate the client and authenticate
    self.gd_client = gdata.contacts.client.ContactsClient(source='google_contact_helper')
    self.gd_client.ClientLogin(user, pw, self.gd_client.source)

  def PrintAllGroups(self):
    feed = self.gd_client.GetGroups()
    for entry in feed.entry:
      print 'Atom Id: %s' % entry.id.text
      print 'Group Name: %s' % entry.title.text

  def GetGroupId(self, group_name):
    """Returns the Group ID of the group with name given by arg"""
    feed = self.gd_client.GetGroups()
    for entry in feed.entry:
      if entry.title.text == group_name:
        return entry.id.text
    return ''

  def PrintAllContacts(self):
    """Retrieves a list of contacts and displays name and primary email."""
    query = gdata.contacts.client.ContactsQuery()
    query.max_results = 1000
    query.group       = self.GetGroupId('System Group: My Contacts')
    feed = self.gd_client.GetContacts(q=query)
    if not feed.entry:
      print '\nNo contacts in feed.\n'
      return
    for i, entry in enumerate(feed.entry):
      if not entry.name is None:
        family_name     = entry.name.family_name is None      and " " or entry.name.family_name.text
        full_name       = entry.name.full_name is None        and " " or entry.name.full_name.text
        given_name      = entry.name.given_name is None       and " " or entry.name.given_name.text
        additional_name = entry.name.additional_name is None  and " " or entry.name.additional_name.text
        print '\n %s \"%s\": \"%s\" \"%s\" \"%s\"' % (i+1, full_name, given_name, family_name, additional_name)

  def FixFullNames(self):
    """Recreate the full_name entry based on family, given and additional name."""
    query = gdata.contacts.client.ContactsQuery()
    query.max_results = 1000
    query.group       = self.GetGroupId('System Group: My Contacts')
    feed = self.gd_client.GetContacts(q=query)
    if not feed.entry:
      print '\nNo contacts in feed.\n'
      return
    for i, entry in enumerate(feed.entry):
      if not entry.name is None:
        family_name     = entry.name.family_name is None      and " " or entry.name.family_name.text
        full_name       = entry.name.full_name is None        and " " or entry.name.full_name.text
        given_name      = entry.name.given_name is None       and " " or entry.name.given_name.text
        additional_name = entry.name.additional_name is None  and " " or entry.name.additional_name.text
        new_full_name   = "%s %s %s" % (family_name, given_name, additional_name)
        new_full_name   = new_full_name.strip()
        print i
        if new_full_name != full_name:
          print 'full name: \"%s\" --> \"%s\"' % (full_name, new_full_name)
          k = raw_input('y to agree')
          if k == 'y':
            entry.name.full_name.text = new_full_name
            try:
              updated_entry = self.gd_client.Update(entry)
              print 'Updated full name: %s' % updated_entry.name.full_name.text
            except gdata.client.RequestError, e:
              if e.status == 412:
                # Etags mismatch: handle the exception.
                pass
          else:
            print 'unchanged full name: \"%s\"' % new_full_name

  def FritzContacts(self, group_name):
    """Retrieves the contacts of a given group and return the element tree formatted in Fritz XML."""
    query = gdata.contacts.client.ContactsQuery()
    query.max_results = 1000
    query.group       = self.GetGroupId(group_name)
    feed = self.gd_client.GetContacts(q=query)
    if not feed.entry:
      print '\nNo contacts in feed.\n'
      return None
    
    root = Element('phonebooks')
    phonebook = SubElement(root, 'phonebook', {'owner':"1", 'name':"Test"})
    
    for i, entry in enumerate(feed.entry):
      if not entry.name is None:
        contact = SubElement(phonebook, 'contact')
        SubElement(contact, 'category')
        person = SubElement(contact,'person')

        # assemble name for entry
        family_name     = entry.name.family_name is None      and " " or entry.name.family_name.text
        given_name      = entry.name.given_name is None       and " " or entry.name.given_name.text
        additional_name = entry.name.additional_name is None  and " " or entry.name.additional_name.text
        new_full_name = "%s %s %s" % (family_name, given_name, additional_name)
        SubElement(person, 'realName').text = new_full_name.strip()

        telephony = SubElement(contact,'telephony')
        for phone_number in entry.phone_number:
          if not (phone_number.rel == gdata.data.FAX_REL
                  or phone_number.rel == gdata.data.HOME_FAX_REL
                  or phone_number.rel == gdata.data.WORK_FAX_REL
                  or phone_number.rel == gdata.data.OTHER_FAX_REL):
            num_type = "home"
            if phone_number.rel == gdata.data.WORK_REL:
              num_type = "work"
            if (phone_number.rel == gdata.data.WORK_MOBILE_REL
                or phone_number.rel == gdata.data.MOBILE_REL):
              num_type = "mobile"
            SubElement(telephony, 'number', {'type':num_type}).text = phone_number.text

        SubElement(contact, 'services')
        SubElement(contact, 'setup')
        SubElement(contact, 'uniqueid').text = str(i)

    return root

  def WriteXmlFile(self, elem, filename):
    """Write the ElementTree.Element into a XML file."""
    # convert element tree to utf-8 and then to unicode
    rough_string = ElementTree.tostring(elem, 'utf-8').decode('utf-8')
    # all unicode strings must be utf-8 encoded before they can be passed to minidom methods
    reparsed     = minidom.parseString(rough_string.encode('utf8'))
    # convert minidom tree to XML utf-8 string and then into unicode string
    pretty_xml   = reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    # print as unicode string
    print pretty_xml
    with codecs.open(filename, 'w', 'utf-8') as f:
      # write unicode string to file encoded as utf-8 
      f.write(pretty_xml)
    f.close()

def main():
  # Parse command line options
  try:
    opts, args = getopt.getopt(sys.argv[1:], '', ['user=', 'pw='])
  except getopt.error, msg:
    print msg
    print 'Usage: ' + __file__ + ' --user [username] --pw [password]'
    sys.exit(2)
    
  if (len(args) > 0):
    print 'Info: given arguments are ignored'

  user = ''
  pw   = ''

  # try fetching the user and passwd from local file
  passwd_file = os.path.expanduser('~/gmail_credential.txt')
  if (len(glob.glob(passwd_file)) == 1):
    with open(passwd_file, 'r') as f:
      lines = f.readlines()
      user = lines[0].rstrip()
      pw   = lines[1].rstrip()
    f.close()

  # Process options
  for option, arg in opts:
    if option == '--user':
      user = arg
    elif option == '--pw':
      pw   = arg

  if (user == '') or (pw == ''):
    print 'No User or Password specified'
    sys.exit(2)
    
  try:
    gc = GoogleContacts(user, pw)
  except gdata.client.BadAuthentication:
    print 'Invalid user credentials given.'
    return

  ## application exampe 1: print all groups and contacts
  #gc.PrintAllGroups()
  #gc.PrintAllContacts()
  
  ## application example 2: export gcontacts into Fritz XML format
  # get contacts from group 'Telefon'
  fritz_xml_elements = gc.FritzContacts('Telefon')
  # write these contacts into a XML file
  gc.WriteXmlFile(fritz_xml_elements, 'FritzContacts.xml')
  
  ## application example 3: fix the full_name entry in all contacts
  gc.FixFullNames()
  

if __name__ == '__main__':
  main()
