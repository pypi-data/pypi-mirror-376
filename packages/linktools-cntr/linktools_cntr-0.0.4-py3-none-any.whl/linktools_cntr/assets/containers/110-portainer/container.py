#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author  : Hu Ji
@file    : deploy.py 
@time    : 2023/05/21
@site    :  
@software: PyCharm 

              ,----------------,              ,---------,
         ,-----------------------,          ,"        ,"|
       ,"                      ,"|        ,"        ,"  |
      +-----------------------+  |      ,"        ,"    |
      |  .-----------------.  |  |     +---------+      |
      |  |                 |  |  |     | -==----'|      |
      |  | $ sudo rm -rf / |  |  |     |         |      |
      |  |                 |  |  |/----|`---=    |      |
      |  |                 |  |  |   ,/|==== ooo |      ;
      |  |                 |  |  |  // |(((( [33]|    ,"
      |  `-----------------'  |," .;'| |((((     |  ,"
      +-----------------------+  ;;  | |         |,"
         /_)______________(_/  //'   | +---------+
    ___________________________/___  `,
   /  oooooooooooooooo  .o.  oooo /,   `,"-----------
  / ==ooooooooooooooo==.o.  ooo= //   ,``--{)B     ,"
 /_==__==========__==_ooo__ooo=_/'   /___________,"
"""
from linktools import Config
from linktools.decorator import cached_property

from linktools_cntr import BaseContainer, ExposeLink


class Container(BaseContainer):

    @cached_property
    def configs(self):
        return dict(
            PORTAINER_TAG="alpine",
            PORTAINER_DOMAIN=self.get_nginx_domain(),
            PORTAINER_EXPOSE_PORT=Config.Property(type=int) | 0,
        )

    @cached_property
    def exposes(self) -> [ExposeLink]:
        return [
            self.expose_public("Portainer", "docker", "Docker管理工具", self.load_nginx_url("PORTAINER_DOMAIN")),
            self.expose_container("Portainer", "docker", "Docker管理工具", self.load_port_url("PORTAINER_EXPOSE_PORT", https=False)),
        ]

    def on_starting(self):
        self.write_nginx_conf(
            domain=self.get_config("PORTAINER_DOMAIN"),
            url="http://portainer:9000"
        )
