# This plugin records the running status of configured docker containers by names.
#
# It requires the docker-py python library. YOu can install it with pip install docker-py
#
# Example collectd config
#<LoadPlugin python>
#  Globals true
#</LoadPlugin>

#<Plugin python>
#    ModulePath "/opt/collectd/plugin"
#    LogTraces true
#    Interactive false
#    Import "docker_collectd"

#    <Module docker_collectd>
#        containers "cont1" "cont22"
#    </Module>
#</Plugin>
#
# With the above config the plugin will check if the containers cont1 and cont2 are in running status and set a 0 or 1 appropriately.

from docker import Client
import collectd
import time

CONTAINERS = []
PLUGIN_NAME = "docker-container"
INTERVAL = 30 # the interval with which the plugin should be run by collectd.

def configure(conf):
  """Receive configuration block. Sets up the global CONTAINERS list.
  Arguments: Takes the collectd Config object (https://collectd.org/documentation/manpages/collectd-python.5.shtml#config).
  Returns: None.
  """
  
  for node in conf.children:
    key = node.key.lower()
    val = node.values
    if key == 'containers':
      global CONTAINERS
      CONTAINERS = val
      collectd.debug('Determining status of the following containers ' + ' '.join(CONTAINERS))
    else:
      collectd.warning('Containers name not set.')

def read(containers):
  """Figures out the running status of the containers.
  Arguments (containers:  A container list.)
  Returns (cont_status: A dict with the key as container and value as running status.)
  """
  
  cont_status = {}
  cli = Client(base_url='unix://var/run/docker.sock')
  running_conts_details = cli.containers(filters={'status': 'running'})
  running_conts = [c['Names'] for c in running_conts_details]
  running_conts_names = [item.lstrip('/') for sublist in running_conts for item in sublist]
  for c in containers:
    if c in running_conts_names:
      cont_status[c] = 1
    else:
      cont_status[c] = 0
  return cont_status

def dispatch_value(key, value):
  """Dispatches a value for the key
  Argumets (key: Container name
            value:  The running status which is either 0 or 1)
  Returns: None.
  """

  val = collectd.Values(type="gauge", plugin=PLUGIN_NAME)
  val.plugin_instance = key
  val.values = [value]
  val.dispatch()

def read_callback():
  
  collectd.debug('Containers ' + ' '.join(CONTAINERS))
  conts = read(CONTAINERS)
  if conts is None:
    return
  for k, v in conts.iteritems():
    dispatch_value(k, v)

# register callbacks
collectd.register_config(configure)
collectd.register_read(read_callback, INTERVAL)

