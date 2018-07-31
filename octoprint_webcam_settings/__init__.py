# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import subprocess
import re


CONTROL_RE = re.compile(r'^\s*(\S+)\s*\((\S+)\)\s*:(.*)$')
MENU_RE = re.compile('^\s*(\S+)\s*:(.*)$')


class WebcamSettingsPlugin(octoprint.plugin.StartupPlugin,
                           octoprint.plugin.TemplatePlugin):
  @staticmethod
  def _try_parse_int(val):
    try:
      return int(val)
    except ValueError:
      return val

  def _load_controls(self):
    output = subprocess.check_output(['v4l2-ctl', '-L'])
    controls = {}
    last_control = None
    for line in output.splitlines():
      parsed_control = CONTROL_RE.match(line)
      if parsed_control:
        name, kind, settings = parsed_control.groups()
        settings = dict(s.split('=', 1) for s in settings.split())
        settings = {k: self._try_parse_int(v) for k, v in settings.iteritems()}
        controls[name] = {'kind': kind, 'settings': settings}
        if kind == 'menu':
          controls[name]['menu'] = {}
        last_control = controls[name]
        continue

      parsed_menu = MENU_RE.match(line)
      if parsed_menu and last_control:
        value, meaning = parsed_menu.groups()
        last_control['menu'][int(value)] = meaning

    self._logger.info("Detected %d webcam controls", len(controls))
    return controls

  def _calc_values(self, name):
    control = self._controls[name]
    if control['kind'] == 'menu':
      return control['menu'].keys()
    elif control['kind'] == 'bool':
      return [0, 1]
    elif control['kind'] == 'int':
      return range(control['min'], control['max'], control['step'])
    else:
      return []

  def _set_control(self, name, value):
    assert name in self._controls
    assert value in self._calc_values(name)
    subprocess.check_call(['v4l2-ctl', '-C', '%s=%s' % (name, value)])

  def on_after_startup(self):
    self._controls = self._load_controls()


__plugin_name__ = 'Webcam Settings'
__plugin_implementation__ = WebcamSettingsPlugin()
