#!/usr/bin/env python

import cmds.init
from repo.configobj import ConfigObj
import db.dump
import os
import repo
from db import SQLLoadError, MigrationFailedError

def add(number, sqlUp, sqlDown, message):
  """Adds a new migration."""
  config = cmds.init.config()
  MIGRATION_DIR = config["migrations_dir"]
  MIGRATION_DIR = os.path.join (repo.repopath(), MIGRATION_DIR)
  PATH = MIGRATION_DIR + "/%s-%s.conf"

  numberWithZeros = str(number).zfill(3)
  messageAlias = message.lower().replace (' ', '_').replace ('.', '').replace ('`', '').replace ("\n", '').replace(':', '')[0:16]
  revision = ConfigObj (PATH % (numberWithZeros, messageAlias))
  revision["number"] = number
  revision["message"] = message
  revision["up"] = sqlUp
  revision["down"] = sqlDown
  revision["author"] = current_user()
  revision.write()
  
def all():
  return [m+1 for m in range(latest_number())]
  
def latest_number():
  """Returns greates migration number available."""
  config = cmds.init.config()
  MIGRATION_DIR = config["migrations_dir"]
  MIGRATION_DIR = os.path.join (repo.repopath(), MIGRATION_DIR)

  migration_numbers = [int(file[0:3]) for file in os.listdir (MIGRATION_DIR)]
  return max (migration_numbers)
  
def current_user():
  """Returns current user."""
  for user_variable in ['USER', 'USERNAME']:
    if user_variable in os.environ:
      return os.environ[user_variable]
  return "Unknown user"
  
class Migration:
  def __init__ (self, number):
    config = cmds.init.config()
    MIGRATION_DIR = config["migrations_dir"]
    MIGRATION_DIR = os.path.join (repo.repopath(), MIGRATION_DIR)

    self.number = ''
    self.message = ''
    self.sqlUp = ''
    self.sqlDown = ''
    self.filename = ''
    self.author = ''
    self.state_to_rollback = db.dump.restore_point()
    
    numberWithZeros = str(number).zfill(3)
    filename = [file for file in os.listdir (MIGRATION_DIR) if file.startswith(numberWithZeros)][0]
    self.__fromFile (MIGRATION_DIR + os.sep + filename)
          
  def __fromFile (self, file):
    def update (config):
      config.write()
      
    config = ConfigObj (file)
    self.number = config["number"]
    self.message = config["message"]
    self.sqlUp = config["up"]
    self.sqlDown = config["down"]
    self.filename = file
    if "author" in config:
      self.author = config["author"]
    else:
      self.author = current_user()
      config["author"] = self.author
      update (config)
    
  def up (self):
    """Executes the up action for migration"""
    try:
      db.dump.load (self.sqlUp)
    except SQLLoadError, error:
      self.rollback(verbose = True, message = error)

  def down (self):
    """Executes the down action for migration"""
    try:
      db.dump.load (self.sqlDown)
    except SQLLoadError, error:
      self.rollback(verbose = True, message = error)

  def rollback (self, verbose = True, message = ''):
    """Rolls back changes to latest state"""
    if verbose:
      print "---"
      print """Migration #%s has failed.""" % (self.number),
      if message:
        print message
      print """Check your migration file (%s) and correct it.""" % self.filename
      print "Rolling back failed migration..."
    db.dump.load (self.state_to_rollback)
    raise MigrationFailedError(migration_number = self.number)
