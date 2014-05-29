What?
=====

This is a simple genealogical data management application.  It differs from
most other applications in that it is a fact-based expert system.  Data is
added into the system as *facts*.  Then you can ask it questions or generate
reports based on the data that is there.

Why?
====

This application suite grew out of a repeated frustration of mine with the
tools that exist in the marketplace.  Many are very nice, but they fall short
when actually entering structured data in a complete manner.  For example,
to add a census record for a family in one application that I used for many
years requires that you:

    #. find a person that the census record identifies
    #. click on the "Add Event" button and fill in the top-level
       information - the event type, the date, and the location
    #. double-click on the new event to edit it
    #. click on the "Add Source" button, scroll through a list of
       known sources to find the appropriate "census" or add a new
       one.  Click "OK".
    #. enter the page number and other location information about
       the census in the generic "authority" or "note" field
    #. close the event
    #. open the "birth" event and identify the new census record as
       proof if there is a match there.
    #. go through a similar series of steps to add an occupation
       record if that information is included
    #. update the "marriage" record identifying the census record as
       proof if there is a match there
    #. go through a similar series of steps to add a "place of
       residence" record if appropriate

Then I get to perform nearly the same steps for **every** person in the
family!

My goal for this suite of software is to make it easy to record facts such
as census records, *known facts*, marriage records, etc. and let the software
do the heavy lifting of linking things together and discovering new facts.

How?
====

The suite of applications will start out as a set of sharp, well-honed,
general purpose command line tools that perform each simple task.  The data
that is entered will be stored in a scalable general purpose database and
a graph database.  The latter is used to *discover* new facts based on the
data.

Eventually, I will graft a web-based interface over top of the backend API
that develops.

Where?
======

**Source**
    http://github.com/dave-shawley/family-tree
**Documentation**
    http://family-tree.readthedocs.org/en/latest/

