from types import StringTypes
from django.contrib.auth import authenticate
from plstackapi.openstack.client import OpenStackClient
from plstackapi.openstack.driver import OpenStackDriver
from plstackapi.core.api.auth import auth_check
from plstackapi.core.models import Sliver, Slice
from plstackapi.core.api.images import _get_images
from plstackapi.core.api.keys import _get_keys
from plstackapi.core.api.slices import _get_slices
from plstackapi.core.api.deployment_networks import _get_deployment_networks
from plstackapi.core.api.nodes import _get_nodes
 

def _get_slivers(filter):
    if isinstance(filter, StringTypes) and filter.isdigit():
        filter = int(filter)
    if isinstance(filter, int):
        slivers = Sliver.objects.filter(id=filter)
    elif isinstance(filter, StringTypes):
        slivers = Sliver.objects.filter(name=filter)
    elif isinstance(filter, dict):
        slivers = Sliver.objects.filter(**filter)
    else:
        slivers = []
    return slivers
 
def add_sliver(auth, fields):
    driver = OpenStackDriver(client = auth_check(auth))
        
    images = _get_images(fields.get('image'))
    if images: fields['image'] = images[0]     
    keys = _get_keys(fields.get('key'))
    if keys: fields['key'] = keys[0]     
    slices = _get_slices(fields.get('slice'))
    if slices: 
        fields['slice'] = slices[0]     
    deployment_networks = _get_deployment_networks(fields.get('deploymentNetwork'))
    if deployment_networks: fields['deploymentNetwork'] = deployment_networks[0]     
    nodes = _get_nodes(fields.get('node'))
    if nodes: fields['node'] = nodes[0]     
    sliver = Sliver(**fields)
    sliver.driver = driver    
    sliver.save()
    return sliver

def update_sliver(auth, sliver, **fields):
    return  

def delete_sliver(auth, filter={}):
    driver = OpenStackDriver(client = auth_check(auth))   
    slivers = _get_slivers(filter)
    for sliver in slivers:
        sliver.driver = driver
        sliver.delete()
    return 1

def get_slivers(auth, filter={}):
    user = authenticate(username=auth.get('username'),
                        password=auth.get('password'))
    if 'slice' in filter:
        slices = _get_slices(filter.get('slice'))
        if slices: filter['slice'] = slices[0]
    slivers = _get_slivers(filter)
    return slivers             
        

    
