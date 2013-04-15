""" Module to get real download url for varias net disk,
    Will automatically import all file in plugins/disk.
"""

import glob, inspect
from os.path import dirname, basename

# import all module and store them in known_brand
known_brand = []
for module_file in glob.glob(dirname(inspect.getfile(inspect.currentframe())) + "/*.py"):
    module_name = basename(module_file)[0:-3]
    if module_name != "__init__" and module_name != "__base__":
        try:
            mod = __import__(module_name, globals(), locals(), [], -1)
            c   = mod.Downloader()
            known_brand.append(c)
            print "Module %s for %s imported" % (module_name, c.brand)
        except ImportError as IE:
            print "Import %s failed, error: %s" %(module_name, repr(IE))

# get brand from url
def get_class(url):
    """ try to determain the brand of an url
        will fallback to http when all test failed.
        take url, and return coresponding Downloader class.
    """
    for c in known_brand:
        if c.url_pattern(url):
            return c
    return None

