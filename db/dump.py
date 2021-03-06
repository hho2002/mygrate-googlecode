#!/usr/bin/env python

from subprocess import Popen, PIPE
import os
import datetime
import cmds.init
from db import SQLLoadError



def restore_point():
  config = cmds.init.config()
  user     = config["db_user"]
  password = config["db_pass"]
  db       = config["db_db"]
  host     = config["db_host"]
  return mysqldump_command ("-u%s %s%s %s --add-drop-table --default-character-set=utf8 %s" % (user, "-p" if password else "", password, "-h"+host if host <> 'localhost' else "", db))

def dump():
  config = cmds.init.config()
  user     = config["db_user"]
  password = config["db_pass"]
  db       = config["db_db"]
  host     = config["db_host"]
  return mysqldump_command ("--no-data --add-lock=false --compact -u%s %s%s %s --default-character-set=utf8 %s" % (user, "-p" if password else "", password, "-h"+host if host <> 'localhost' else "", db))

def load (sql):
  config = cmds.init.config()
  user     = config["db_user"]
  password = config["db_pass"]
  db       = config["db_db"]
  host     = config["db_host"]

  tempfile = ".temp-mygrate-%s" % str(datetime.time()).replace (':', '_')
  f = open (tempfile, 'w')
  f.write (sql)
  f.close()
  
  (output, errors) = mysql_command ("-u%s %s%s %s --default-character-set=utf8 %s < %s" % (user, "-p" if password else "", password, "-h"+host if host <> 'localhost' else "", db, tempfile))
  os.unlink(tempfile)
  if errors:
    raise SQLLoadError (sql = sql, errors = errors)
  return True
  
def mysql_command (cmd):
  config = cmds.init.config()
  mysql_path = config["mysql"] if "mysql" in config else "mysql"
  process = Popen("%s %s" % (mysql_path, cmd), shell=True, stdout=PIPE, stderr=PIPE)
  out = process.stdout.read()
  err = process.stderr.read()
  return (out, err)
  
def mysqldump_command (cmd):
  config = cmds.init.config()
  mysqldump_path = config["mysqldump"] if "mysqldump" in config else "mysqldump"
  process = Popen("%s %s" % (mysqldump_path, cmd), shell=True, stdout=PIPE)
  out = process.stdout.read()
  return out
