import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
# filename = "/Users/derwent/Documents/GitHub/LEDPortalSimulator/tools/export_structure.py"
filename = "/Users/derwent/Documents/GitHub/LEDPortalSimulator/tools/light_layout.py"
exec(compile(open(filename).read(), filename, 'exec'))
