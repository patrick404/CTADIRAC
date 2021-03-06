"""
  Simple Wrapper on the Job class to handle Read_Cta Analysis
"""

__RCSID__ = "$Id$"

# generic imports
import os, json, collections
# DIRAC imports
import DIRAC
from DIRAC.Interfaces.API.Job import Job
from DIRAC.Resources.Catalog.FileCatalogClient import FileCatalogClient

class ReadCta3Job( Job ) :
  """ Job extension class for Read_Cta Analysis,
      takes care of running read_cta
  """
        
  def __init__( self, cpuTime = 432000 ):
    """ Constructor
    
    Keyword arguments:
    cpuTime -- max cpu time allowed for the job
    """
    Job.__init__( self )
    self.setCPUTime( cpuTime )
    # defaults
    self.setName('ReadCta_Analysis')
    self.package='corsika_simhessarray'
    self.version = '2015-10-20'
    self.basepath = '/vo.cta.in2p3.fr/MC/PROD3/'
    self.outputpattern = './*simtel-dst0.gz'
    self.fcc = FileCatalogClient()
    self.metadata = collections.OrderedDict()
    self.filemetadata = {}
    self.jobGroupID = 1

  def setPackage(self, package):
    """ Set package name : e.g. 'corsika_simhessarray'
    
    Parameters:
    package -- corsika_simhessarray
    """
    self.package=package

  def setVersion(self, version):
    """ Set software version number : e.g. v500-prod3v1
    
    Parameters:
    version -- evndisplay package version number
    """
    self.version=version
    
  def setReadCtaMD( self, path ):
    """ Set read_cta meta data starting from path metadata
    
    Parameters:
    path -- path from which get meta data
    """
    # # Get simtel meta data from path
    res = self.fcc.getFileUserMetadata( path )
    simtelMD = res['Value']

    # # Set read_cta directory meta data
    self.metadata['array_layout'] = simtelMD['array_layout']
    self.metadata['site'] = simtelMD['site']
    self.metadata['particle'] = simtelMD['particle']
    self.metadata['phiP'] = simtelMD['phiP']
    self.metadata['thetaP'] = simtelMD['thetaP']
    self.metadata['analysis_prog'] = 'read_cta'
    self.metadata['analysis_prog_version'] = self.version


  def setupWorkflow(self, debug=False):
    """ Setup job workflow by defining the sequence of all executables
        All parameters shall have been defined before that method is called.
    """

    # step 1 -- to be removed -- debug only
    iStep = 1
    if debug:
        lsStep = self.setExecutable( '/bin/ls -alhtr', logFile = 'LS_Init_Log.txt' )
        lsStep['Value']['name']='Step%i_LS_Init'%iStep
        lsStep['Value']['descr_short']='list files in working directory'
        iStep+=1
      
    # step 2  
    swStep = self.setExecutable( 'cta-prod3-setupsw',
                              arguments='%s %s'% (self.package, self.version),\
                              logFile='SetupSoftware_Log.txt')
    swStep['Value']['name'] = 'Step%i_SetupSoftware' % iStep
    swStep['Value']['descr_short'] = 'Setup software'
    iStep+=1

    # step 2bis
    # arguments are nbFiles=0 (not used) and fileSize=100kB
    inStep = self.setExecutable( 'cta-prod3-verifysteps', \
                              arguments = 'analysisinputs 0 100', \
                              logFile = 'Verify_ReadCtaInputs_Log.txt' )
    inStep['Value']['name'] = 'Step%i_VerifyReadCtaInputs' % iStep
    inStep['Value']['descr_short'] = 'Verify ReadCta Inputs'
    iStep += 1

    # step 3
    res = DIRAC.sourceEnv(600, ['prod3_types'], {} )
    read_cta_opts=res['outputEnv']['read_cta_opts']

    rctaStep = self.setExecutable( './dirac_prod3_read_cta', \
                                   arguments = "-q -r 4 -u --min-trg-tel 2 %s" % (read_cta_opts),
                                logFile = 'ReadCta_Log.txt' )
    rctaStep['Value']['name'] = 'Step%i_ReadCta' % iStep
    rctaStep['Value']['descr_short'] = 'Run ReadCta'
    iStep += 1

    # step 4
    # ## the order of the metadata dictionary is important, since it's used to build the directory structure
    mdjson = json.dumps( self.metadata )

    metadatafield = {'array_layout':'VARCHAR(128)', 'site':'VARCHAR(128)', 'particle':'VARCHAR(128)', \
                         'phiP':'float', 'thetaP': 'float', 'analysis_prog':'VARCHAR(128)', 'analysis_prog_version':'VARCHAR(128)'}

    mdfieldjson = json.dumps( metadatafield )

    fmdjson = json.dumps( self.filemetadata )

    ## Upload Data files
    dmStep = self.setExecutable( 'cta-analysis-managedata.py',
                              arguments = "'%s' '%s' '%s' %s '%s' %s" % ( mdjson, mdfieldjson, fmdjson, self.basepath, self.outputpattern, self.package ),
                              logFile = 'DataManagement_Log.txt' )
    dmStep['Value']['name'] = 'Step%i_DataManagement' % iStep
    dmStep['Value']['descr_short'] = 'Save files to SE and register them in DFC'
    iStep += 1

    # Upload Histogram files and use 'Log' as outputType
    self.outputpattern = './*hdata-dst0.gz'

    dmStep = self.setExecutable( 'cta-analysis-managedata.py',
                              arguments = "'%s' '%s' '%s' %s '%s' %s %s" % ( mdjson, mdfieldjson, fmdjson, self.basepath, self.outputpattern, self.package, 'Log'),
                              logFile = 'DataManagement_Log.txt' )
    dmStep['Value']['name'] = 'Step%i_DataManagement' % iStep
    dmStep['Value']['descr_short'] = 'Save files to SE and register them in DFC'
    iStep += 1
