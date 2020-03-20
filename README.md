# LEDPortalSimulator
LXStudio Simulator and animations for Flavius' LED Art Installation

## Usage Python Tools

If you are using VSCode, it's helpful to point your editor to use the Python included in Blender.
Determine your blender Python location, and add it to your `.vscode/settings.json`

```json
{
  ...
  "python.pythonPath": "/Applications/Blender.app/Contents/Resources/2.80/python/bin/python3.7m"
}
```

To run the scripts on your model file, you will need to install the script's dependencies into
Blender's internal Python environment.

```bash
/Applications/Blender.app/Contents/Resources/2.80/python/bin/python3.7m -m pip install -r tools/requirements.txt
```

Open your blender file from a terminal. If blender was installed with `brew cask` you will have
access to a `blender` command, otherwise you can just call the full name of the blender executable.

```bash
blender your_model.blend
```

Then, in the Scripting tab, open the file `script_wrapper.py` and change the file path to point to
the script you want to run, the click `Run Script`. The script will output to the terminal from
which Blender was initially run.
