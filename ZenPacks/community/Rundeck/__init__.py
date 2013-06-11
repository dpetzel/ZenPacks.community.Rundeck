import Globals

import logging
logger = logging.getLogger('.'.join(['zen', __name__]))

from Products.ZenModel.ZenPack import ZenPack as ZenPackBase
from Products.ZenUtils.Utils import zenPath, unused

import os

unused(Globals)


class ZenPack(ZenPackBase):
    """
    Loader for ZenPacks.community.Rundeck.
    """
    
    packZProperties = [
        ('zRundeckAPIPort', 4440, 'int'),
        ('zRundeckAPIToken', '', 'password'),
        ('zRundeckAPIScheme', 'http', 'string')
        ]
    
    def install(self, app):
        super(ZenPack, self).install(app)
        self.symlinkPlugin()

    def remove(self, app, leaveObjects=False):
        if not leaveObjects:
            self.removePluginSymlink()

        super(ZenPack, self).remove(app, leaveObjects=leaveObjects)
    
    def symlinkPlugin(self):
        os.system('ln -sf %s/check_rundeck.py %s/' %
            (self.path('libexec'), zenPath('libexec')))

    def removePluginSymlink(self):
        os.system('rm -f %s/check_rundeck.py' % (zenPath('libexec')))