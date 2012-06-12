#!/usr/bin/python
#
# https://developers.google.com/google-apps/contacts/v3/

#import sys
#import getopt
#import atom
#import gdata.contacts.data
import gdata.contacts.client

from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from xml.dom import minidom

class GoogleContacts(object):
  """GoogleContacts object provides helper methods to access Google contacts."""

  def __init__(self):
    """Constructor for the GoogleContacts object."""
    # customize the class HERE
    user = 'Georg.Drenkhahn@googlemail.com'
    pw   = 'oprlmknbrbumphcn'
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

  def ListAllContacts(self):
    """Retrieves a list of contacts and displays name and primary email."""
    query = gdata.contacts.client.ContactsQuery()
    query.max_results = 1000
    # system group: my contacts
    query.group = self.GetGroupId('System Group: My Contacts')
    feed = self.gd_client.GetContacts(q=query)
    if not feed.entry:
      print '\nNo contacts in feed.\n'
      return 0
    for i, entry in enumerate(feed.entry):
      if not entry.name is None:
        family_name     = entry.name.family_name is None      and " " or entry.name.family_name.text
        full_name       = entry.name.full_name is None        and " " or entry.name.full_name.text
        given_name      = entry.name.given_name is None       and " " or entry.name.given_name.text
        additional_name = entry.name.additional_name is None  and " " or entry.name.additional_name.text
        #print '\n %s \"%s\": \"%s\" \"%s\" \"%s\"' % (i+1, full_name, given_name, family_name, additional_name)
        new_full_name = "%s %s %s" % (family_name, given_name, additional_name)
        new_full_name = new_full_name.strip()
        print i
        if new_full_name != full_name:
          print 'old full name: \"%s\"' % full_name
          print 'new full name: \"%s\"' % new_full_name
        else:
          print 'unchanged full name: \"%s\"' % new_full_name
    return len(feed.entry)

  def FritzContacts(self):
    """Retrieves a list of contacts and create Fritz contacts."""
    query = gdata.contacts.client.ContactsQuery()
    query.max_results = 1000
    # group: Telefon
    query.group = self.GetGroupId('Telefon')
    feed = self.gd_client.GetContacts(q=query)
    if not feed.entry:
      print '\nNo contacts in feed.\n'
      return None
    
    root = Element('phonebooks')
    phonebook = SubElement(root, 'phonebook', {'owner':"1", 'name':"Test"})
    
    for i, entry in enumerate(feed.entry):
      if not entry.name is None:
        family_name     = entry.name.family_name is None      and " " or entry.name.family_name.text
        #full_name       = entry.name.full_name is None        and " " or entry.name.full_name.text
        given_name      = entry.name.given_name is None       and " " or entry.name.given_name.text
        additional_name = entry.name.additional_name is None  and " " or entry.name.additional_name.text
        new_full_name = "%s %s %s" % (family_name, given_name, additional_name)
        new_full_name = new_full_name.strip()

        contact = SubElement(phonebook, 'contact')
        SubElement(contact, 'category')
        person = SubElement(contact,'person')
        SubElement(person,'realName').text = new_full_name
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

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def main():
  # Parse command line options
#  try:
#    opts, args = getopt.getopt(sys.argv[1:], '', ['user=', 'pw='])
#  except getopt.error, msg:
#    print 'google_contact_helper.py --user [username] --pw [password]'
#    sys.exit(2)

  try:
    gc = GoogleContacts()
  except gdata.client.BadAuthentication:
    print 'Invalid user credentials given.'
    return

  #gc.PrintAllGroups()
  #gc.ListAllContacts()
  fritz_xml = gc.FritzContacts()
  print prettify(fritz_xml)

if __name__ == '__main__':
  main()
