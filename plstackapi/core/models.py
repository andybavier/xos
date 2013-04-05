import os
from django.db import models
from plstackapi.openstack.driver import OpenStackDriver

# Create your models here.

class PlCoreBase(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Role(PlCoreBase):

    ROLE_CHOICES = (('admin', 'Admin'), ('pi', 'Principle Investigator'), ('user','User'))
    role_type = models.CharField(max_length=80, unique=True, choices=ROLE_CHOICES)

    def __unicode__(self):  return u'%s' % (self.role_type)

    def save(self):
        if not self.id:
            self.created = datetime.date.today()
        self.updated = datetime.datetime.today()
        super(Role, self).save()

class Site(PlCoreBase):
    tenant_id = models.CharField(max_length=200, help_text="Keystone tenant id")
    name = models.CharField(max_length=200, help_text="Name for this Site")
    site_url = models.URLField(null=True, blank=True, max_length=512, help_text="Site's Home URL Page")
    enabled = models.BooleanField(default=True, help_text="Status for this Site")
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    login_base = models.CharField(max_length=50, help_text="Prefix for Slices associated with this Site")
    is_public = models.BooleanField(default=True, help_text="Indicates the visibility of this site to other members")
    abbreviated_name = models.CharField(max_length=80)

    def __unicode__(self):  return u'%s' % (self.name)

    def save(self, *args, **kwargs):
        driver  = OpenStackDriver()
        if not self.id:
            tenant = driver.create_tenant(tenant_name=self.login_base, 
                                          description=self.name, 
                                          enabled=self.enabled)
            self.tenant_id = tenant.id
        else:
            # update record
            self.driver.update_tenant(self.tenant_id, name=self.login_base,
                                      description=self.name, enabled=self.enabled)
        super(Site, self).save(*args, **kwargs)

    def delete(self, *args, **kwds):
        # delete keystone tenant
        driver  = OpenStackDriver()
        driver.delete_tenant(self.tenant_id)
        super(Site, self).delete(*args, **kwargs)

class User(PlCoreBase):
    user_id = models.CharField(max_length=256, unique=True)
    firstname = models.CharField(help_text="person's given name", max_length=200)
    lastname = models.CharField(help_text="person's surname", max_length=200)
    email = models.EmailField(help_text="e-mail address")
    phone = models.CharField(help_text="phone number contact", max_length=100)
    user_url = models.URLField()
    site = models.ForeignKey(Site, related_name='site_user', verbose_name="Site this user will be homed too")

    def __unicode__(self):  return u'%s' % (self.email)

    def save(self):
        if not self.id:
            self.created = datetime.date.today()
        self.updated = datetime.datetime.today()
        super(User, self).save()

class SitePrivilege(PlCoreBase):

    user = models.ForeignKey('User')
    site = models.ForeignKey('Site')
    role = models.ForeignKey('Role')

    def __unicode__(self):  return u'%s %s %s' % (self.site, self.user, self.role)

    def save(self):
        if not self.id:
            self.created = datetime.date.today()
        self.updated = datetime.datetime.today()
        super(SitePrivilege, self).save()

class Slice(PlCoreBase):
    tenant_id = models.CharField(max_length=200, help_text="Keystone tenant id")
    name = models.CharField(help_text="The Name of the Slice", max_length=80)
    enabled = models.BooleanField(default=True, help_text="Status for this Slice")
    SLICE_CHOICES = (('plc', 'PLC'), ('delegated', 'Delegated'), ('controller','Controller'), ('none','None'))
    instantiation = models.CharField(help_text="The instantiation type of the slice", max_length=80, choices=SLICE_CHOICES)
    omf_friendly = models.BooleanField()
    description=models.TextField(blank=True,help_text="High level description of the slice and expected activities", max_length=1024)
    slice_url = models.URLField(blank=True, max_length=512)
    site = models.ForeignKey(Site, related_name='site_slice', help_text="The Site this Node belongs too")

    def __unicode__(self):  return u'%s' % (self.name)

    def save(self, *args, **kwds):
        # sync keystone tenant
        driver  = OpenStackDriver()

        if not self.id:
            tenant = driver.create_tenant(tenant_name=self.name,
                                          description=self.description,
                                          enabled=self.enabled)
            self.tenant_id = tenant.id
            
            # create router
            driver.create_router(name=self.name)
            
            # create a network  
            driver.create_network(name=self.name)

        else:
            # update record
            self.driver.update_tenant(self.tenant_id, name=self.name,
                                      description=self.description, enabled=self.enabled)
        super(Slice, self).save(*args, **kwds)

    def delete(self, *args, **kwds):
        # delete keystone tenant
        driver  = OpenStackDriver()
        driver.delete_tenant(self.tenant_id)
        super(Slice, self).delete(*args, **kwds)

class SliceMembership(PlCoreBase):
    user = models.ForeignKey('User')
    slice = models.ForeignKey('Slice')
    role = models.ForeignKey('Role')

    def __unicode__(self):  return u'%s %s %s' % (self.slice, self.user, self.role)

    def save(self):
        if not self.id:
            self.created = datetime.date.today()
        self.updated = datetime.datetime.today()
        super(SliceMembership, self).save()

class SubNet(PlCoreBase):
    subnet_id = models.CharField(max_length=256, unique=True)
    cidr = models.CharField(max_length=20)
    ip_version = models.IntegerField()
    start = models.IPAddressField()
    end = models.IPAddressField()
    slice = models.ForeignKey(Slice, related_name='slice_subnet')

    def __unicode__(self):  return u'%s' % (self.name)

    def save(self, *args, **kwargs):
        driver  = OpenStackDriver()
        if not self.id:
            subnet = driver.create_subnet(network_name=self.slice.name,
                                          cidr_ip = self.cidr,
                                          ip_version=self.ip_version,
                                          start = self.start,
                                          end = self.end)

            self.subnet_id = subnet.id

        super(SubNet, self).save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        # delete quantum network
        driver  = OpenStackDriver()
        driver.delete_subnet(self.subnet_id)
        super(SubNet, self).delete(*args, **kwargs)



class DeploymentNetwork(PlCoreBase):
    name = models.CharField(max_length=200, unique=True, help_text="Name of the Deployment Network")

    def __unicode__(self):  return u'%s' % (self.name)

class SiteDeploymentNetwork(PlCoreBase):
    class Meta:
        unique_together = ['site', 'deploymentNetwork']

    site = models.ForeignKey(Site, related_name='deploymentNetworks')
    deploymentNetwork = models.ForeignKey(DeploymentNetwork, related_name='sites')
    name = models.CharField(default="Blah", max_length=100)
    

    def __unicode__(self):  return u'%s::%s' % (self.site, self.deploymentNetwork)


class Node(PlCoreBase):
    name = models.CharField(max_length=200, unique=True, help_text="Name of the Node")
    siteDeploymentNetwork = models.ForeignKey(SiteDeploymentNetwork, help_text="The Site and Deployment Network this Node belongs too.")

    def __unicode__(self):  return u'%s' % (self.name)

class Image(PlCoreBase):
    image_id = models.CharField(max_length=256, unique=True)
    name = models.CharField(max_length=256, unique=True)
    disk_format = models.CharField(max_length=256)
    container_format = models.CharField(max_length=256)

    def __unicode__(self):  return u'%s' % (self.name)


class Flavor(PlCoreBase):
    flavor_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=256, unique=True)
    memory_mb = models.IntegerField()
    disk_gb = models.IntegerField()
    vcpus = models.IntegerField()

    def __unicode__(self):  return u'%s' % (self.name)

class Key(PlCoreBase):
    name = models.CharField(max_length=256, unique=True)
    key = models.CharField(max_length=512)
    type = models.CharField(max_length=256)
    blacklisted = models.BooleanField()
    user = models.ForeignKey(User)

    def __unicode__(self):  return u'%s' % (self.name)

    def save(self, *args, **kwds):
        driver  = OpenStackDriver()
        if not self.id:
            keypair = driver.create_keypair(name=self.name, key=self.key)
        super(Key, self).save(*args, **kwds)

    def delete(self, *args, **kwds):
        driver  = OpenStackDriver()
        driver.delete_keypair(self.name)
        super(Key, self).delete(*args, **kwds)



class Sliver(PlCoreBase):
    instance_id = models.CharField(max_length=200, help_text="Nova instance id")    
    name = models.CharField(max_length=200, help_text="Sliver name")
    flavor = models.ForeignKey(Flavor, related_name='sliver_flavor')
    image = models.ForeignKey(Image, related_name='sliver_image') 
    key = models.ForeignKey(Key, related_name='sliver_key')        
    slice = models.ForeignKey(Slice, related_name='sliver_slice')
    siteDeploymentNetwork = models.ForeignKey(SiteDeploymentNetwork, related_name='sliver_deployment')
    node = models.ForeignKey(Node, related_name='sliver_node')

    def __unicode__(self):  return u'%s::%s' % (self.slice, self.siteDeploymentNetwork)

    def save(self, *args, **kwds):
        driver  = OpenStackDriver()
        instance = driver.spawn_instances(name=self.name,
                                          keyname=self.name,
                                          hostnames=self.node.name,
                                          flavor=self.flavor.name,
                                          image=self.image.name)
        self.instance_id = instance.id
        super(Sliver, self).save(*args, **kwds)

    def delete(self, *args, **kwds):
        driver  = OpenStackDriver()
        driver.destroy_instance(name=self.name, id=self.instance_id)
        super(Sliver, self).delete(*args, **kwds)

