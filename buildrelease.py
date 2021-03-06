import os
import sys
import json
from datetime import datetime, date

import lux
import clean
import setup

clean.run()

assert lux.VERSION[3] == 'final'

with open('CHANGELOG.rst', 'r') as f:
    changelog = f.read()

top = changelog.split('\n')[0]
version_date = top.split(' - ')
assert len(version_date) == 2, 'Top of CHANGELOG.rst must be version and date'
version, datestr = version_date
dt = datetime.strptime(datestr, '%Y-%b-%d').date()
assert dt == date.today()

assert version == 'Ver. %s' % lux.__version__

with open('package.json', 'r') as f:
    pkg = json.loads(f.read())

pkg['version'] = lux.__version__
pkg['description'] = lux.__doc__

with open('package.json', 'w') as f:
    f.write(json.dumps(pkg, indent=4))

# Run setup.py
script = os.path.abspath(setup.__file__)
sys.argv = [script, 'sdist'] + sys.argv[1:]
setup.run()


print('%s %s ready!' % (pkg['name'], lux.__version__))
