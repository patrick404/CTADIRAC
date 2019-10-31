import json
# # from DIRAC
from DIRAC import S_OK, S_ERROR
# from CTADIRAC
from CTADIRAC.DataManagementSystem.private.JSONUtils import DMSEncoder


class ProvBase(object):

  def toJSON( self ):
    """ Returns the JSON formated string that describes the agent """
    try:
      jsonStr = json.dumps( self, cls = DMSEncoder )
      return S_OK( jsonStr )
    except Exception as e:
      return S_ERROR( str( e ) )

  def _jsonData( self, attrNames ):
    """ Returns the JSON formated string that describes the agent """
    jsonData = {}
    for attrName in attrNames :
      # id might not be set since it is managed by SQLAlchemy
      if not hasattr( self, attrName ):
        continue
      value = getattr( self, attrName )
      jsonData[attrName] = value

    return jsonData

class Entity(ProvBase):

  def __init__( self, id = None, classType = None, name = None, location = None, generatedAtTime = None, \
                invalidatedAtTime = None, comment = None, entityDescription_id = None ):

    self.id = id
    self.classType = classType
    self.name = name
    self.location = location
    self.generatedAtTime = generatedAtTime
    self.invalidatedAtTime = invalidatedAtTime
    self.comment = comment
    self.entityDescription_id = entityDescription_id

  def _getJSONData( self ):
    """ Returns the data that have to be serialized by JSON """

    attrNames = ['id','classType','name','location','generatedAtTime','invalidatedAtTime','comment', \
                 'entityDescription_id' ]
    return self._jsonData(attrNames)

class DatasetEntity(Entity):

  def __init__( self, id = None, classType = None, name = None, location = None, generatedAtTime = None, \
                invalidatedAtTime = None, comment = None, entityDescription_id = None ):

    self.id = id
    self.classType = classType
    self.name = name
    self.location = location
    self.generatedAtTime = generatedAtTime
    self.invalidatedAtTime = invalidatedAtTime
    self.comment = comment
    self.entityDescription_id = entityDescription_id

class EntityDescription(ProvBase):

  def __init__( self, id = None, name = None, type = None, description = None, doculink = None, classType = None):

    self.id = id
    self.name = name
    self.type = type
    self.description = description
    self.doculink = doculink
    self.classType = classType

  def _getJSONData( self ):
    """ Returns the data that have to be serialized by JSON """

    attrNames = ['id','name','type','description','doculink','classType']
    return self._jsonData(attrNames)


class ActivityDescription(ProvBase):

  def __init__( self, id = None, name = None, version = None, description = None, \
                type = None, subtype = None, doculink = None):

    self.id = id
    self.name = name
    self.version = version
    self.description = description
    self.type = type
    self.subtype = subtype
    self.doculink = doculink


  def _getJSONData( self ):
    """ Returns the data that have to be serialized by JSON """

    attrNames = ['id','name','type','subtype','version','doculink','description']
    return self._jsonData(attrNames)

class Activity(ProvBase):

  def __init__( self, id = None, name = None, startTime = None, endTime = None, comment = None, \
                activityDescription_id = None):

    self.id = id
    self.name = name
    self.startTime = startTime
    self.endTime = endTime
    self.comment = comment
    self.activityDescription_id = activityDescription_id

  def _getJSONData( self ):
    """ Returns the data that have to be serialized by JSON """

    attrNames = ['id','name','startTime','endTime','comment','activityDescription_id']
    return self._jsonData(attrNames)

class WasAssociatedWith(ProvBase):

  def __init__( self, id = None, activity = None, agent = None, role = None):

    self.id = id
    self.activity = activity
    self.agent = agent
    self.role = role

  def _getJSONData( self ):
    """ Returns the data that have to be serialized by JSON """

    attrNames = ['id','activity','agent','role']
    return self._jsonData(attrNames)


class DatasetDescription(EntityDescription):

  def __init__( self, id = None, name = None, type = None, description = None, doculink = None, classType = None, \
                contentType = None):

    EntityDescription.__init__(self, id = id, name = name, type = type, description = description, \
                               doculink = doculink, classType = classType)
    self.contentType = contentType

  def _getJSONData(self):
    """ Returns the data that have to be serialized by JSON """

    attrNames = ['id', 'name', 'type', 'description', 'doculink', 'contentType']
    return self._jsonData(attrNames)

class ValueDescription(EntityDescription):

  def __init__( self, id = None, name = None, type = None, description = None, doculink = None, classType = None,\
                valueType = None, unit = None, ucd = None, utype = None, min = None, max = None, \
                default = None, options = None):
    EntityDescription.__init__(self, id = id, name = name, type = type, description = description, \
                               doculink = doculink, classType = classType)
    self.valueType = valueType
    self.unit = unit
    self.ucd = ucd
    self.utype = utype
    self.min = min
    self.max = max
    self.default = default
    self.options = options

  def _getJSONData(self):
    """ Returns the data that have to be serialized by JSON """

    attrNames = ['id', 'name', 'type', 'description', 'doculink', 'valueType', 'unit', 'ucd', 'utype', 'min', 'max', 'default', 'options']
    return self._jsonData(attrNames)

class UsageDescription(ProvBase):

  def __init__( self, id = None, role = None, description = None, type = None, multiplicity = 1, \
                activityDescription_id = None, entityDescription_id = None):

    self.id = id
    self.role = role
    self.description = description
    self.type = type
    self.multiplicity = multiplicity
    self.activityDescription_id = activityDescription_id
    self.entityDescription_id = entityDescription_id

  def _getJSONData( self ):
    """ Returns the data that have to be serialized by JSON """

    attrNames = ['id','role','description','type','multiplicity','activityDescription_id','entityDescription_id']
    return self._jsonData(attrNames)

class GenerationDescription(ProvBase):

  def __init__( self, id = None, role = None, description = None, type = None, multiplicity = 1, \
                activityDescription_id = None, entityDescription_id = None):

    self.id = id
    self.role = role
    self.description = description
    self.type = type
    self.multiplicity = multiplicity
    self.activityDescription_id = activityDescription_id
    self.entityDescription_id = entityDescription_id

  def _getJSONData( self ):
    """ Returns the data that have to be serialized by JSON """

    attrNames = ['id','role','description','type','multiplicity','activityDescription_id','entityDescription_id']
    return self._jsonData(attrNames)

class WasAttributedTo(ProvBase):

  def __init__( self, id = None, entity = None, agent = None, role = None ):

    self.id = id
    self.entity = entity
    self.agent = agent
    self.role = role

  def _getJSONData( self ):
    """ Returns the data that have to be serialized by JSON """

    attrNames = ['id','entity','agent','role']
    return self._jsonData(attrNames)

class Agent(ProvBase):

  def __init__( self, id = None, name = None, type = None, email = None, affiliation = None, phone = None, \
                address = None):

    self.id = id
    self.name = name
    self.type = type
    self.email = email
    self.affiliation = affiliation
    self.phone = phone
    self.address = address

  def _getJSONData( self ):
    """ Returns the data that have to be serialized by JSON """

    attrNames = ["id", "name", "type", "email", "affiliation", "phone", "address"]
    return self._jsonData(attrNames)

class Used(ProvBase):

  def __init__( self, id = None, role = None, time = None, activity_id = None, entity_id = None , usageDescription_id = None ):

    self.id = id
    self.role = role
    self.time = time
    self.activity_id = activity_id
    self.entity_id = entity_id
    self.usageDescription_id = usageDescription_id

  def _getJSONData( self ):
    """ Returns the data that have to be serialized by JSON """

    attrNames = ['id','role','time','activity_id','entity_id','usageDescription_id']
    return self._jsonData(attrNames)

class WasGeneratedBy(ProvBase):

  def __init__( self, id = None, role = None, activity_id = None, entity_id = None , generationDescription_id = None ):

    self.id = id
    self.role = role
    self.activity_id = activity_id
    self.entity_id = entity_id
    self.generationDescription_id = generationDescription_id

  def _getJSONData( self ):
    """ Returns the data that have to be serialized by JSON """

    attrNames = ['id','role','activity_id','entity_id','generationDescription_id']
    return self._jsonData(attrNames)

class ValueEntity(Entity):

  def __init__( self, id = None, classType = None, name = None, location = None, generatedAtTime = None, \
                invalidatedAtTime = None, comment = None, entityDescription_id = None ):

    self.id = id
    self.classType = classType
    self.name = name
    self.location = location
    self.generatedAtTime = generatedAtTime
    self.invalidatedAtTime = invalidatedAtTime
    self.comment = comment
    self.entityDescription_id = entityDescription_id


