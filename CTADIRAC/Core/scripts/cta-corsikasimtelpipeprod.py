#!/usr/bin/env python
import DIRAC
import os

def setRunNumber( optionValue ):
  global run_number
  run_number = optionValue.split('ParametricParameters=')[1]
  return DIRAC.S_OK()

def setCorsikaTemplate( optionValue ):
  global corsikaTemplate
  corsikaTemplate = optionValue
  return DIRAC.S_OK()

def setExecutable( optionValue ):
  global executable
  executable = optionValue
  return DIRAC.S_OK()

def setVersion( optionValue ):
  global version
  version = optionValue
  return DIRAC.S_OK()

def setStorageElement( optionValue ):
  global storage_element
  storage_element = optionValue
  return DIRAC.S_OK()

def sendOutputCorsika(stdid,line):
  logfilename = executable + '.log'
  f = open( logfilename,'a')
  f.write(line)
  f.write('\n')
  f.close()

def sendOutput(stdid,line):
  DIRAC.gLogger.notice(line)

def main():

  from DIRAC.Core.Base import Script

  Script.registerSwitch( "p:", "run_number=", "Run Number", setRunNumber )
  Script.registerSwitch( "T:", "template=", "Template", setCorsikaTemplate )
  Script.registerSwitch( "E:", "executable=", "Executable", setExecutable )
  Script.registerSwitch( "V:", "version=", "Version", setVersion )
  Script.registerSwitch( "D:", "storage_element=", "Storage Element", setStorageElement )

  from DIRAC.Resources.Catalog.FileCatalogClient import FileCatalogClient
  from DIRAC.Resources.Catalog.FileCatalog import FileCatalog

  Script.parseCommandLine()
  global fcc, fcL, storage_element
  
  from CTADIRAC.Core.Workflow.Modules.CorsikaApp import CorsikaApp
  from CTADIRAC.Core.Utilities.SoftwareInstallation import checkSoftwarePackage
  from CTADIRAC.Core.Utilities.SoftwareInstallation import installSoftwarePackage
  from CTADIRAC.Core.Utilities.SoftwareInstallation import installSoftwareEnviron
  from CTADIRAC.Core.Utilities.SoftwareInstallation import localArea
  from CTADIRAC.Core.Utilities.SoftwareInstallation import sharedArea
  from CTADIRAC.Core.Utilities.SoftwareInstallation import workingArea
  from DIRAC.Core.Utilities.Subprocess import systemCall
  from DIRAC.WorkloadManagementSystem.Client.JobReport import JobReport
  
  jobID = os.environ['JOBID']
  jobID = int( jobID )
  jobReport = JobReport( jobID )

  CorsikaSimtelPack = 'corsika_simhessarray/' + version + '/corsika_simhessarray'

  packs = [CorsikaSimtelPack]

  for package in packs:
    DIRAC.gLogger.notice( 'Checking:', package )
    if sharedArea:
      if checkSoftwarePackage( package, sharedArea() )['OK']:
        DIRAC.gLogger.notice( 'Package found in Shared Area:', package )
        installSoftwareEnviron( package, workingArea() )
        packageTuple =  package.split('/')
        corsika_subdir = sharedArea() + '/' + packageTuple[0] + '/' + version  
        cmd = 'cp -u -r ' + corsika_subdir + '/* .'       
        os.system(cmd)
        continue
    if workingArea:
      if checkSoftwarePackage( package, workingArea() )['OK']:
        DIRAC.gLogger.notice( 'Package found in Local Area:', package )
        continue
      if installSoftwarePackage( package, workingArea() )['OK']:
      ############## compile #############################
        if version == 'prod-2_21122012':
          cmdTuple = ['./build_all','prod2','qgs2']
        else:
          cmdTuple = ['./build_all','ultra','qgs2']
        ret = systemCall( 0, cmdTuple, sendOutput)
        if not ret['OK']:
          DIRAC.gLogger.error( 'Failed to compile')
          DIRAC.exit( -1 )
        continue

    DIRAC.gLogger.error( 'Check Failed for software package:', package )
    DIRAC.gLogger.error( 'Software package not available')
    DIRAC.exit( -1 )  

 ###########
  ## Checking MD coherence
  fc = FileCatalog('LcgFileCatalog')
  res = fc._getCatalogConfigDetails('DIRACFileCatalog')
  print 'DFC CatalogConfigDetails:',res
  res = fc._getCatalogConfigDetails('LcgFileCatalog')
  print 'LCG CatalogConfigDetails:',res
  
  fcc = FileCatalogClient()
  fcL = FileCatalog('LcgFileCatalog')
  
  from DIRAC.Interfaces.API.Dirac import Dirac
  dirac = Dirac()
  
  #############
  simtelConfigFilesPath = 'sim_telarray/multi'
  simtelConfigFile = simtelConfigFilesPath + '/multi_cta-ultra5.cfg'                          
  createGlobalsFromConfigFiles('prodConfigFile', corsikaTemplate, simtelConfigFile)
  
  ######################Building prod Directory Metadata #######################
  resultCreateProdDirMD = createProdFileSystAndMD()  
  if not resultCreateProdDirMD['OK']:
    DIRAC.gLogger.error( 'Failed to create prod Directory MD')
    jobReport.setApplicationStatus('Failed to create prod Directory MD')
    DIRAC.gLogger.error('Metadata coherence problem, no file produced')
    DIRAC.exit( -1 )
  else:
    print 'prod Directory MD successfully created'

  ######################Building corsika Directory Metadata #######################
  
  resultCreateCorsikaDirMD = createCorsikaFileSystAndMD()  
  if not resultCreateCorsikaDirMD['OK']:
    DIRAC.gLogger.error( 'Failed to create corsika Directory MD')
    jobReport.setApplicationStatus('Failed to create corsika Directory MD')
    DIRAC.gLogger.error('Metadata coherence problem, no corsikaFile produced')
    DIRAC.exit( -1 )
  else:
    print 'corsika Directory MD successfully created'
  
  ############ Producing Corsika File
  cs = CorsikaApp()
  cs.setSoftwarePackage(CorsikaSimtelPack)
  cs.csExe = executable
  cs.csArguments = ['--run-number',run_number,'--run','corsika',corsikaTemplate]
  corsikaReturnCode = cs.execute()
  
  if corsikaReturnCode != 0:
    DIRAC.gLogger.error( 'Corsika Application: Failed')
    jobReport.setApplicationStatus('Corsika Application: Failed')
    DIRAC.exit( -1 )

########################  
## files spread in 1000-runs subDirectories
  runNum = int(run_number)
  subRunNumber = '%03d'%runNum
  runNumModMille = runNum%1000
  runNumTrunc = (runNum - runNumModMille)/1000
  runNumSeriesDir = '%03dxxx'%runNumTrunc
  print 'runNumSeriesDir=',runNumSeriesDir

#### create a file to DISABLE_WATCHDOG_CPU_WALLCLOCK_CHECK ################
  f = open('DISABLE_WATCHDOG_CPU_WALLCLOCK_CHECK', 'w' )
  f.close()

############ Producing SimTel File
 ######################Building simtel Directory Metadata #######################
  
  resultCreateSimtelDirMD = createSimtelFileSystAndMD()  
  if not resultCreateSimtelDirMD['OK']:
    DIRAC.gLogger.error( 'Failed to create simtelArray Directory MD')
    jobReport.setApplicationStatus('Failed to create simtelArray Directory MD')
    DIRAC.gLogger.error('Metadata coherence problem, no simtelArray File produced')
    DIRAC.exit( -1 )
  else:
    print 'simtel Directory MD successfully created'
  
  simtelFileName = particle + '_' + thetaP + '_' + phiP + '_alt' + obslev + '_' + 'run' + run_number + '.simtel.gz'
  cmd = 'mv Data/sim_telarray/' + simtelExecName + '/0.0deg/Data/*.simtel.gz ' + simtelFileName
  if(os.system(cmd)):
    DIRAC.exit( -1 )
    
  simtelOutFileDir = os.path.join(simtelDirPath,'Data',runNumSeriesDir)
  simtelOutFileLFN = os.path.join(simtelOutFileDir,simtelFileName)
  simtelRunNumberSeriesDirExist = fcc.isDirectory(simtelOutFileDir)['Value']['Successful'][simtelOutFileDir]
  newSimtelRunFileSeriesDir = (simtelRunNumberSeriesDirExist != True)  # if new runFileSeries, will need to add new MD

  simtelLogFileName = particle + '_' + thetaP + '_' + phiP + '_alt' + obslev + '_' + 'run' + run_number + '.log.gz'
  cmd = 'mv Data/sim_telarray/' + simtelExecName + '/0.0deg/Log/*.log.gz ' + simtelLogFileName
  if(os.system(cmd)):
    DIRAC.exit( -1 )

  simtelOutLogFileDir = os.path.join(simtelDirPath,'Log',runNumSeriesDir)
  simtelOutLogFileLFN = os.path.join(simtelOutLogFileDir,simtelLogFileName)

  simtelHistFileName = particle + '_' + thetaP + '_' + phiP + '_alt' + obslev + '_' + 'run' + run_number + '.hdata.gz'
  cmd = 'mv Data/sim_telarray/' + simtelExecName + '/0.0deg/Histograms/*.hdata.gz ' + simtelHistFileName
  if(os.system(cmd)):
    DIRAC.exit( -1 )
  simtelOutHistFileDir = os.path.join(simtelDirPath,'Histograms',runNumSeriesDir)
  simtelOutHistFileLFN = os.path.join(simtelOutHistFileDir,simtelHistFileName)
  
################################################  
  DIRAC.gLogger.notice( 'Put and register simtel File in LFC and DFC:', simtelOutFileLFN)
  ret = dirac.addFile( simtelOutFileLFN, simtelFileName, storage_element )   

  res = CheckCatalogCoherence(simtelOutFileLFN)
  if res != DIRAC.S_OK:
    DIRAC.gLogger.error('Job failed: Catalog Coherence problem found')
    jobReport.setApplicationStatus('OutputData Upload Error')
    DIRAC.exit( -1 )
    
  if not ret['OK']:
    DIRAC.gLogger.error('Error during addFile call:', ret['Message'])
    jobReport.setApplicationStatus('OutputData Upload Error')
    DIRAC.exit( -1 )
######################################################################

  DIRAC.gLogger.notice( 'Put and register simtel Log File in LFC and DFC:', simtelOutLogFileLFN)
  ret = dirac.addFile( simtelOutLogFileLFN, simtelLogFileName, storage_element )

  res = CheckCatalogCoherence(simtelOutLogFileLFN)
  if res != DIRAC.S_OK:
    DIRAC.gLogger.error('Job failed: Catalog Coherence problem found')
    jobReport.setApplicationStatus('OutputData Upload Error')
    DIRAC.exit( -1 )
     
  if not ret['OK']:
    DIRAC.gLogger.error('Error during addFile call:', ret['Message'])
    jobReport.setApplicationStatus('OutputData Upload Error')
    DIRAC.exit( -1 )
######################################################################

  DIRAC.gLogger.notice( 'Put and register simtel Histo File in LFC and DFC:', simtelOutHistFileLFN)
  ret = dirac.addFile( simtelOutHistFileLFN, simtelHistFileName, storage_element )

  res = CheckCatalogCoherence(simtelOutHistFileLFN)
  if res != DIRAC.S_OK:
    DIRAC.gLogger.error('Job failed: Catalog Coherence problem found')
    jobReport.setApplicationStatus('OutputData Upload Error')
    DIRAC.exit( -1 )
     
  if not ret['OK']:
    DIRAC.gLogger.error('Error during addFile call:', ret['Message'])
    jobReport.setApplicationStatus('OutputData Upload Error')
    DIRAC.exit( -1 )
######################################################################
    
  if newSimtelRunFileSeriesDir:
    insertRunFileSeriesMD(simtelOutFileDir,runNumTrunc)
    insertRunFileSeriesMD(simtelOutLogFileDir,runNumTrunc)
    insertRunFileSeriesMD(simtelOutHistFileDir,runNumTrunc)
    
###### simtel File level metadata ############################################

  simtelFileMD={}
  simtelFileMD['runNumber'] = int(run_number)
  simtelFileMD['jobID'] = jobID
  simtelFileMD['simtelReturnCode'] = corsikaReturnCode
  
  result = fcc.setMetadata(simtelOutFileLFN,simtelFileMD)
  print "result setMetadata=",result
  if not result['OK']:
    print 'ResultSetMetadata:',result['Message']

  result = fcc.setMetadata(simtelOutLogFileLFN,simtelFileMD)
  print "result setMetadata=",result
  if not result['OK']:
    print 'ResultSetMetadata:',result['Message']

  result = fcc.setMetadata(simtelOutHistFileLFN,simtelFileMD)
  print "result setMetadata=",result
  if not result['OK']:
    print 'ResultSetMetadata:',result['Message']
    
  DIRAC.exit()


def CheckCatalogCoherence(fileLFN):
####Checking and restablishing catalog coherence #####################  
  res = fcc.getReplicas(fileLFN)  
  ndfc = len(res['Value']['Successful'])
  if ndfc!=0:
    DIRAC.gLogger.notice('Found in DFC:',fileLFN)
  res = fcL.getReplicas(fileLFN)
  nlfc = len(res['Value']['Successful'])
  if nlfc!=0:
    DIRAC.gLogger.notice('Found in LFC:',fileLFN)
  if ndfc>nlfc:
    DIRAC.gLogger.error('Catalogs are not coherent: removing file from DFC',fileLFN)
    res = fcc.removeFile(fileLFN)
    return DIRAC.S_ERROR
  elif ndfc<nlfc:
    DIRAC.gLogger.error('Catalogs are not coherent: removing file from LFC',fileLFN)
    res = fcL.removeFile(fileLFN)
    return DIRAC.S_ERROR
  elif (ndfc==0 and nlfc==0):
   DIRAC.gLogger.error('File not found in DFC and LFC:',fileLFN)
   return DIRAC.S_ERROR
    
  return DIRAC.S_OK
     

def createGlobalsFromConfigFiles(prodConfigFileName, corsikaConfigFileName, simtelConfigFileName):

  global prodName
  global thetaP
  global phiP
  global particle
  global energyInfo
  global viewCone
  global pathroot
  global nbShowers
  global simtelOffset
  global prodDirPath
  global corsikaDirPath
  global corsikaParticleDirPath
  global simtelDirPath
  global corsikaOutputFileName
  global simtelExecName
  global corsikaProdVersion
  global simtelProdVersion
  global obslev

  # Getting MD Values from Config Files:
  prodKEYWORDS =  ['prodName','simtelExeName','pathroot']
  dictProdKW = fileToKWDict(prodConfigFileName,prodKEYWORDS)

  corsikaKEYWORDS = ['THETAP', 'PHIP', 'PRMPAR', 'ESLOPE' , 'ERANGE', 'VIEWCONE','NSHOW','TELFIL','OBSLEV']
  dictCorsikaKW = fileToKWDict(corsikaConfigFileName,corsikaKEYWORDS)

  simtelKEYWORDS = ['env offset']

  # Formatting MD values retrieved in configFiles
  prodName = dictProdKW['prodName'][0]
  corsikaProdVersion = version + '_corsika'
  simtelProdVersion = version + '_simtel'
  thetaP = str(float(dictCorsikaKW['THETAP'][0]))
  phiP = str(float(dictCorsikaKW['PHIP'][0]))
  obslev = str(float(dictCorsikaKW['OBSLEV'][0])/100.)#why on earth is this in cm....
  nbShowers = str(int(dictCorsikaKW['NSHOW'][0]))
  corsikaOutputFileName = dictCorsikaKW['TELFIL'][0]  
  simtelExecName = dictProdKW['simtelExeName'][0]
  
  #building simtelArray Offset
  dictSimtelKW={}
  simtelConfigFile = open(simtelConfigFileName, "r").readlines()
  for line in simtelConfigFile:
    lineSplitEqual = line.split('=')
    isAComment = '#' in lineSplitEqual[0].split()
    for word in lineSplitEqual:
      if (word in simtelKEYWORDS and not isAComment) :
        offset = lineSplitEqual[1].split()[0]
        dictSimtelKW[word] = offset
  simtelOffset = dictSimtelKW['env offset']
  
  #building viewCone
  viewConeRange = dictCorsikaKW['VIEWCONE']
  viewCone = str(float(viewConeRange[1]))
    
  #building ParticleName
  dictParticleCode={}
  dictParticleCode['1'] = 'gamma'
  dictParticleCode['14'] = 'proton'
  dictParticleCode['3'] = 'electron'
  dictParticleCode['402'] = 'helium'
  dictParticleCode['1407'] = 'nitrogen'
  dictParticleCode['2814'] = 'silicon'
  dictParticleCode['5626'] = 'iron'
  particleCode = dictCorsikaKW['PRMPAR'][0]
  particle = dictParticleCode[particleCode]
  if viewCone=='0.0':
    particle+="_ptsrc"

  #building energy info:
  eslope = dictCorsikaKW['ESLOPE'][0]
  eRange = dictCorsikaKW['ERANGE']
  emin = eRange[0]
  emax = eRange[1]
  energyInfo = eslope + '_' + emin + '-' + emax
  
  pathroot = dictProdKW['pathroot'][0]
  #building full prod, corsika and simtel Directories path
  prodDirPath = os.path.join(pathroot,prodName)
  corsikaDirPath = os.path.join(prodDirPath,corsikaProdVersion)
  corsikaParticleDirPath = os.path.join(corsikaDirPath,particle)
  simtelDirPath = os.path.join(corsikaParticleDirPath,simtelProdVersion)
  
def fileToKWDict (fileName, keywordsList):    
  #print 'parsing %s...' % fileName
  dict={}
  configFile = open(fileName, "r").readlines()
  for line in configFile:
    if (len(line.split())>0):
      for word in line.split():
        if line.split()[0] is not '*' and word in keywordsList:
          lineSplit = line.split()
          lenLineSplit = len(lineSplit)
          value = lineSplit[1:lenLineSplit]
          dict[word] = value
  return dict


def createIndexes(indexesTypesDict):
  #CLAUDIA ToBeDone: only if they don't already exist: waiting for Release update
  for mdField in indexesTypesDict.keys():
    mdFieldType = indexesTypesDict[mdField]
    result = fcc.addMetadataField(mdField,mdFieldType)
    print 'result addMetadataField %s: %s' % (mdField,result)

def createDirAndInsertMD(dirPath, requiredDirMD):
  # if directory already exist, verify if metadata already exist.  If not, create directory and associated MD
  print 'starting... createDirAndInsertMD(%s)' % dirPath
########## ricardo ##########################################
  dirExists = fcc.isDirectory(dirPath)
  if not dirExists['OK']:
    print dirExists['Message']
    return dirExists
  dirExists = dirExists['Value']['Successful'][dirPath]
############################################################
  print 'dirExist result',dirExists
  if (dirExists):
    print 'Directory already exists'
################# ricardo #################################
    dirMD = fcc.getDirectoryMetadata(dirPath)
    if not dirMD['OK']:
      print dirMD['Message']
      return dirMD
    dirMD = dirMD[ 'Value' ]

    #verify if all the MDvalues already exist, if not, insert their value
    mdToAdd={}
    for mdkey,mdvalue in requiredDirMD.iteritems():
      if mdkey not in dirMD:
        mdToAdd[mdkey] = requiredDirMD[mdkey]     
      else:
        test = (str(dirMD[mdkey]) == str(mdvalue))

        if (test == False):
          print 'metadata key exists, but values are not coherent'
          return DIRAC.S_ERROR('MD')
        else:
          print 'metadata key exist, and values are coherent'

    if len(mdToAdd) > 0:
      result = fcc.setMetadata(dirPath,mdToAdd)
      print "%d metadata added" % len(mdToAdd)
    else:
      print 'no MD needed to be added'
  else:
    print 'New directory, creating path '
    res = fcc.createDirectory(dirPath)
    print "createDir res:", res
    # insert Directory level MD:
    result = fcc.setMetadata(dirPath,requiredDirMD)
    print 'result setMetadataDir:',result
  return DIRAC.S_OK
  

def insertRunFileSeriesMD(runNumSeriesPath,runNumSeries):
  runNumSeriesDirMD={}
  runNumSeriesDirMD['runNumSeries'] = runNumSeries * 1000
  fcc.setMetadata(runNumSeriesPath,runNumSeriesDirMD)
  
def createProdDirIndexes():
  # before creating indexes, it would be fine to know what are those that already exist in the DB
  # Creating INDEXES in DFC DB
  prodDirMDFields={}
  prodDirMDFields['lastRunNumber'] = 'int'
  createIndexes(prodDirMDFields)    
  
def createProdFileSystAndMD():
  # before creating indexes, it would be fine to know what are those that already exist in the DB
  # Creating INDEXES in DFC DB
  prodDirMDFields={}
  prodDirMDFields['prodName'] = 'VARCHAR(128)'
  createIndexes(prodDirMDFields)  
  
  # Adding Directory level metadata Values to DFC
  prodDirMD={}
  prodDirMD['prodName'] = prodName
    
  res = createDirAndInsertMD(prodDirPath, prodDirMD)  
  if res != DIRAC.S_OK:
    return DIRAC.S_ERROR ('Problem creating Prod Directory MD ')
        
  return DIRAC.S_OK ('Prod Directory MD successfully created')
  
def createCorsikaFileSystAndMD():
  # before creating indexes, it would be fine to know what are those that already exist in the DB
  # Creating INDEXES in DFC DB
  corsikaDirMDFields={}
  corsikaDirMDFields['prodName'] = 'VARCHAR(128)'
  corsikaDirMDFields['thetaP'] = 'float'
  corsikaDirMDFields['phiP'] = 'float'
  corsikaDirMDFields['altitude'] = 'float'
  corsikaDirMDFields['particle'] = 'VARCHAR(128)'  
  corsikaDirMDFields['energyInfo'] = 'VARCHAR(128)'
  corsikaDirMDFields['viewCone'] = 'float'
  corsikaDirMDFields['corsikaProdVersion'] = 'VARCHAR(128)'
  corsikaDirMDFields['nbShowers'] = 'int'  
  corsikaDirMDFields['outputType'] = 'VARCHAR(128)'
  corsikaDirMDFields['runNumSeries'] = 'int'  
  
  createIndexes(corsikaDirMDFields)  
  
  # Adding Directory level metadata Values to DFC
  corsikaDirMD={}
  corsikaDirMD['thetaP'] = thetaP
  corsikaDirMD['phiP'] = phiP
  corsikaDirMD['altitude'] = obslev
  corsikaDirMD['energyInfo'] = energyInfo
  corsikaDirMD['corsikaProdVersion'] = corsikaProdVersion

  res = createDirAndInsertMD(corsikaDirPath, corsikaDirMD)  
  if res != DIRAC.S_OK:
    return DIRAC.S_ERROR ('Problem creating Corsika Directory MD ')
    
  corsikaParticleDirMD={}
  corsikaParticleDirMD['particle'] = particle
  corsikaParticleDirMD['viewCone'] = viewCone
   
  res = createDirAndInsertMD(corsikaParticleDirPath, corsikaParticleDirMD)  
  if res != DIRAC.S_OK:
    return DIRAC.S_ERROR ('Problem creating Corsika Particle Directory MD ')

  return DIRAC.S_OK ('Corsika Directory MD successfully created')

def createSimtelFileSystAndMD():
  # Creating INDEXES in DFC DB
  simtelDirMDFields={}
  simtelDirMDFields['simtelArrayProdVersion'] = 'VARCHAR(128)'
  simtelDirMDFields['offset'] = 'float'
  createIndexes(simtelDirMDFields)  
  
  # Adding Directory level metadata Values to DFC
  simtelDirMD={}
  simtelDirMD['simtelArrayProdVersion'] = simtelProdVersion
  simtelOffsetCorr = simtelOffset[1:-1]
  simtelDirMD['offset'] = float(simtelOffsetCorr)

  res = createDirAndInsertMD(simtelDirPath, simtelDirMD)
  if res != DIRAC.S_OK:
    return DIRAC.S_ERROR ('MD Error: Problem creating Simtel Directory MD ')
    
  simtelDataDirPath = os.path.join(simtelDirPath,'Data')
  simtelDataDirMD={}
  simtelDataDirMD['outputType'] = 'Data'
  res = createDirAndInsertMD(simtelDataDirPath, simtelDataDirMD)  
  if res != DIRAC.S_OK:
    return DIRAC.S_ERROR ('Problem creating Simtel Data Directory MD ')

  simtelLogDirPath = os.path.join(simtelDirPath,'Log')
  simtelLogDirMD={}
  simtelLogDirMD['outputType'] = 'Log'
  res = createDirAndInsertMD(simtelLogDirPath, simtelLogDirMD)  
  if res != DIRAC.S_OK:
    return DIRAC.S_ERROR ('Problem creating Simtel Log Directory MD ')

  simtelHistoDirPath = os.path.join(simtelDirPath,'Histograms')
  simtelHistoDirMD={}
  simtelHistoDirMD['outputType'] = 'Histo'
  res = createDirAndInsertMD(simtelHistoDirPath, simtelHistoDirMD)  
  if res != DIRAC.S_OK:
    return DIRAC.S_ERROR ('Problem creating Simtel Histo Directory MD ')
    
  return DIRAC.S_OK ('Simtel Directory MD successfully created')


if __name__ == '__main__':

  try:
    main()
  except Exception:
    DIRAC.gLogger.exception()
    DIRAC.exit( -1 )