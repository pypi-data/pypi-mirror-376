# Copyright 2020 AUI, Inc. Washington DC, USA
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
this module will be included in the api
"""

def measures_update(path=None, version=None, force=False, measures_site=None, logger=None, auto_update_rules=False, use_astron_obs_table=False, verbose=None):
    """
    Update or install the IERS data used for measures calculations from measures_site into path.
    
    Original IERS data source used by each of the recommended measures sites
    is here: https://www.iers.org/IERS/EN/DataProducts/data.html

    If no update is necessary then this function will silently return.

    The verbose argument controls the level of information provided by this function when the data
    are unchanged for expected reasons. A level of 0 outputs nothing. A
    value of 1 sends any output to the logger and a value of 2 logs and prints the information.
    The default value of the verbose argument is taken from the casaconfig_verbose config
    value (defaults to 1). Error messages are always logged and printed.

    CASA maintains a separate Observatories table which is available in the casarundata
    collection through pull_data and data_update. The Observatories table found at measures_site
    is not installed by measures_update and any Observatories file at path will not be changed
    by using this function. This behavior can be changed by setting force and use_astron_obs_table
    both to True (use_astron_obs_table is ignored when force is False).

    A text file (readme.txt in the geodetic directory in path) records the measures version string,
    the measures site that was used and the date when that version was installed in path.

    If path is None then config.measurespath is used.

    If the version requested matches the one in that text file then this function does
    nothing unless force is True.

    If a specific version is not requested (the default) and the modification time of that text
    file is less than the measures_update_interval config value (days) before now then this function 
    does nothing unless force is True. When this function checks for a more recent version and finds 
    that the installed version is the most recent one then the modification time of that text file 
    is changed to the current time even though nothing has changed in path. This limits the 
    number of attempts to update the measures data (including checking
    for more recent data) to once every measures_update_interval days. When the force argument 
    is True and a specific version is not requested then this function always checks for the 
    latest version. The measures_update_interval is always used as an int type (including
    any truncation of the actual value in config if not an integer).

    The measures_site is a single URL or a list of URLs to use to find the measures tar file
    to use in the update. See measures_available for more details on how that parameter
    is used.

    If a specific version is requested then that must match a file in the list returned
    by measures_available. The version is usually unique at each measures_site and so care
    may need to be taken when requesting a specific version to ensure that it's available at 
    measures_site. If measures_site is a list and a specific version is requested then
    measures_update will try and find that version in each measures_site in that list, using
    the first site that has that version.

    When auto_update_rules is True then path must exist and contain the expected readme.txt file.
    Path must be owned by the user, force must be False, and the version must be None. This 
    option is used during casatools initialization when measures_auto_update is True. Automatic 
    updating happens during casatools initialization so that the updated measures are in place 
    before any tool needs to use them.

    Using measures_update after casatools has started should always be followed by exiting 
    and restarting casa (or the casatools module if modular casa components are being used).

    A file lock is used to prevent more that one data update (pull_data, measures_update,
    or data_update) from updating any files in path at the same time. When locked, the 
    lock file (data_update.lock in path) contains information about the process that
    has the lock. When measures_update gets the lock it checks the readme.txt file in path
    to make sure that an update is still necessary (if force is True then an update 
    always happens). If the lock file is not empty then a previous update of path (pull_data,
    data_update, or measures_update) did not exit as expected and the contents of path are
    suspect. In that case, an error will be reported and nothing will be updated. The lock
    file can be checked to see the details of when that file was locked. The lock file can be
    removed and measures_update can be tried again. It may be safest in that case to remove path
    completely or use a different path and use pull_data to install a fresh copy of the
    desired version.

    Care should be used when using measures_update outside of the normal automatic
    update that other casa sessions are not using the same measures at the same time,
    especially if they may also be starting at that time. If a specific version is
    requested or force is True there is a risk that the measures may be updated while
    one of those other sessions are trying to load the same measures data, leading to
    unpredictable results. The lock file will prevent simultaneous updates from
    happening but if each simultaneous update eventually updates the same measures
    location (because force is True or the updates are requesting different versions)
    then the measures that any of those simultaneous casatools modules sees is 
    unpredictable. Avoid multiple, simultaneous updates outside of the automatic
    update process.

    **Note:** during auto updates, measures_update requires that the expected 
    readme.txt file already exists in the geodetic directory at path. If that file does 
    not exist or can not be interpreted as expected then measures_update will 
    return without updating any data.

    **Note:** if auto_update_rules is True the user must own path (in addition to having 
    read and write permissions there). The version must then also be None and the force option 
    must be False.

    **Note:** During use outside of auto updates, if path does not exist it will be created
    by this function.

    **Note:** During use outside of auto updates, if the readme.txt file exists but can not
    be read as expected **OR** that file does not exist but the contents of path appear to
    contain measures data (table names in the expected locations) then this function will
    print messages describing that and exit without changing anything at path. Using
    a force value of True will disable this check and install measures at path even if path
    is not empty or the readme.txt file can not be read. This use of force should be used
    with caution.

    Parameters
       - path (str=None) - Folder path to place updated measures data. Must contain a valid geodetic/readme.txt. If not set then config.measurespath is used.
       - version (str=None) - Version of measures data to retrieve (usually in the form of WSRT_Measures_yyyymmdd-160001.ztar, see measures_available). Default None retrieves the latest.
       - force (bool=False) - If True, always re-download the measures data. Default False will not download measures data if updated within the past day unless the version parameter is specified and different from what was last downloaded.
       - measures_site(str or list of str = None) - Each value is a URL where measures tar files are found. If measures_site is a list then the elements are used in order until a list can be assembled. Default None uses config.measures_site.
       - logger (casatools.logsink=None) - Instance of the casalogger to use for writing messages. Default None writes messages to the terminal
       - auto_update_rules (bool=False) - If True then the user must be the owner of path, version must be None, and force must be False.
       - use_astron_obs_table (bool=False) - If True and force is also True then keep the Observatories table found in the Measures tar tarball (possibly overwriting the Observatories table from casarundata).
       - verbose (int=None) - Level of output, 0 is none, 1 is to logger, 2 is to logger and terminal, defaults to config.casaconfig_verbose.
        
    Returns
       None

    Raises
       - casaconfig.AutoUpdatesNotAllowed - raised when path does not exists as a directory or is not owned by the user when auto_update_rules is True
       - casaconfig.BadLock - raised when the lock file was not empty when found
       - casaconfig.BadReadme - raised when something unexpected is found in the readme or the readme changed after an update is in progress
       - casaconfig.NoReadme - raised when the readme.txt file is not found at path (path also may not exist)
       - casaconfig.NotWritable - raised when the user does not have permission to write to path
       - casaconfig.NoNetwork - raised by measuers_available or when getting the lock file if there is no network.
       - casaconfig.RemoteError - raised by measures_available when the remote list of measures could not be fetched, not due to no network.
       - casaconfig.UnsetMeasurespath - raised when path is None and has not been set in config
       - Exception - raised when something unexpected happened while updating measures
    
    """
    import os
    from datetime import datetime
    import sys

    import tarfile
    import re

    from casaconfig import measures_available
    from casaconfig import AutoUpdatesNotAllowed, UnsetMeasurespath, RemoteError, NotWritable, BadReadme, BadLock, NoReadme, NoNetwork

    from .print_log_messages import print_log_messages
    from .get_data_lock import get_data_lock
    from .get_data_info import get_data_info
    from .measures_available import measures_available
    from .do_untar_url import do_untar_url

    from .. import config as _config

    if path is None:
        path = _config.measurespath

    if path is None:
        raise UnsetMeasurespath('measures_update: path is None and has not been set in config.measurespath. Provide a valid path and retry.')

    if measures_site is None:
        measures_site = _config.measures_site

    if verbose is None:
        verbose = _config.casaconfig_verbose

    path = os.path.expanduser(path)

    if auto_update_rules:
        if version is not None:
            print_log_messages('auto_update_rules requires that version be None', logger, True)
            return
        if force:
            print_log_messages('force must be False when auto_update_rules is True', logger, True)
            return
        if (not os.path.isdir(path)) or (os.stat(path).st_uid != os.getuid()):
            raise AutoUpdatesNotAllowed("measures_update: path must exist as a directory and it must be owned by the user, path = %s" % path)
    
    if not os.path.exists(path):
        # make dirs all the way down, if possible
        os.makedirs(path)
        
    currentVersion = None
    ageRecent = False
    currentSite = None

    # first, does this look like it needs to be updated

    # get any existing measures readme information
    readmeInfo = get_data_info(path, logger, type='measures')
    if readmeInfo is not None:
        currentVersion = readmeInfo['version']
        currentSite = readmeInfo['site']
        if readmeInfo['age'] is not None:
            ageRecent = readmeInfo['age'] < int(_config.measures_update_interval)

    if not force:
        # don't check for new version if the age is less than measures_update_interval days
        if version is None and ageRecent:
            print_log_messages('measures_update: version installed or checked less than %s day(s) ago, nothing updated or checked' % int(_config.measures_update_interval), logger, verbose=verbose)
            return
        
        if currentVersion is not None:
            # don't overwrite something that looks bad unless forced to do so
            if 'invalid' in currentVersion:
                raise NoReadme('measures_update: no measures readme.txt file found at %s. Nothing updated or checked.' % path)

            if 'error' in currentVersion:
                msg = "measures_update: the measures readme.txt file at %s could not be read as expected, an update can not proceed unless force is True" % path
                # add any additional error message, anything after the first ":" if is found
                colonIndex = currentVersion.find(":")
                if colonIndex != -1:
                    msg += "; " + currentVersion[colonIndex+1:]
                raise BadReadme(msg)

            # don't overwrite something that looks like valid measures data unless forced to do so
            if 'unknown' in currentVersion:
                print_log_messages('measures_update: the measures data at %s is not maintained by casaconfig and so it can not be updated unless force is True' % path, logger, True)
                return

        checkVersion = version
        if checkVersion is None:
            # get the current most recent version
            try:
                # if measures_site is a list, measures_available will return the list from the appropriate site in that list
                # that might not be the same site recorded with currentVersion, but that's OK for this update step
                # the currentVersion is already old enough to trigger this check for a more recent version
                checkVersion = measures_available(measures_site=measures_site)[-1]
            except NoNetwork as exc:
                # no network, no point in continuing, just reraise
                raise exc
            except RemoteError as exc:
                # bad network?, no point in continuing, just reraise
                raise exc                
            except:
                # unsure what happened, leave it at none, which will trigger an update attempt, which might work
                print("unexpected excption in measuress_available")
                import traceback
                traceback.print_exc()
                pass

        # don't re-download the same data
        if (checkVersion is not None) and (checkVersion == currentVersion):
            print_log_messages('measures_update: requested version already installed in %s' % path, logger, verbose=verbose)
            # update the age of the readme to now
            readme_path = os.path.join(path,'geodetic/readme.txt')
            # readme_path should already exist if it's here
            os.utime(readme_path)
            
            return

        # don't do anything unless the Observatories table is already installed as expected
        obsTabPath = os.path.join(path,'geodetic/Observatories')
        if not os.path.isdir(obsTabPath):
            msgs = []
            msgs.append("Error: the Observatories table was not found as expected in %s" % path)
            msgs.append("Either install casarundata first or set use_astron_obs_table and force to be True when using measures_update.")
            msgs.append("Note that the Observatories table provided in the measures tarfile is not the same as that maintained by CASA")
            print_log_messages(msgs, logger, True)
            return
        
    # path must be writable with execute bit set
    if (not os.access(path, os.W_OK | os.X_OK)) :
        raise NotWritable('measures_update: No permission to write to path, cannot update : %s' % path)

    # an update needs to happen

    # lock the measures_update.lock file
    lock_fd = None
    clean_lock = True    # set to false if the contents are actively being update and the lock file should not be cleaned one exception
    try:
        print_log_messages('measures_update ... acquiring the lock ... ', logger, verbose=verbose)

        # the BadLock exception that may happen here is caught below
        lock_fd = get_data_lock(path, 'measures_update')

        do_update = force
        
        if not do_update:
            # recheck the readme file, another update may have already happened before the lock was obtained
            currentVersion = None
            ageRecent = False
            
            readmeInfo = get_data_info(path, logger, type='measures')
            if readmeInfo is not None:
                currentVersion = readmeInfo['version']
                if readmeInfo['age'] is not None:
                    ageRecent = readmeInfo['age'] < int(_config.measures_update_interval)

            if (version is not None) and (version == currentVersion):
                print_log_messages('The requested measures version is already installed in %s, using version %s' % (path, currentVersion), logger, verbose=verbose)
            elif (version is None) and ageRecent:
                print_log_messages('The latest measures version was checked recently in %s, using version %s' % (path, currentVersion), logger, verbose=verbose)
            else:
                # final check for problems before updating
                if not force and readmeInfo is not None and (version=='invalid' or version=='unknown'):
                    # at this point, this indicates something is unexpectedly wrong, do not continue
                    # this exception is caught below
                    # do not clean up the lock file
                    clean_lock = False
                    raise BadReadme('measures_update: something unexpected has changed in the path location, can not continue')
                else:
                    # an update is needed
                    do_update = True

        if do_update:
            if force:
                print_log_messages('A measures update has been requested by the force argument', logger, verbose=verbose)

            print_log_messages('  ... finding available measures ...', logger, verbose=verbose)

            target = None
            site = None

            # if a specific version has been request AND measures_site is a list with more than one value
            # then find the site with that version in it. Turn off logging in measures_available calls
            # here as the age of the site doesn't matter
            if version is not None and isinstance(measures_site, list) and len(measures_site) > 1:
                target = version
                for this_site in measures_site:
                    files = measures_available(measures_site=this_site, logger=None)
                    # make sure that site is excluded from files before target is checked
                    files = files[1:]
                    if target in files:
                        site = this_site
                        break
                if site is None:
                    print_log_messages("measures_update can't find specfied version %s at any of the sites in the measures_site list" % target, logger, True)
                # else site and  target are set
            else:
                # if measure_available sorts out what site to use if it's a list with more than one element
                # a specific version probably needs to use a specific site to make it work
                # if a specific version has been requested then the age of the site isn't an issue, turn logging off
                this_logger = logger if version is None else None
                files = measures_available(measures_site=measures_site, logger=this_logger)
                site = files[0]
                # this makes sure that the site is exclude from files before target is checked.
                files = files[1:]

                # target filename to download
                # for the non-force unspecified version case this can only get here if the age is > 1 day so there should be a newer version
                # but that isn't checked - this could install a version that's already installed
                target = files[-1] if version is None else version
                if target not in files:
                    print_log_messages("measures_update can't find specified version %s at site %s" % (target,site), logger, True)
                    # unset site here to signal nothing to extract
                    site = None

            if site is not None:
                # there are files to extract
                print_log_messages('  ... downloading %s from %s to %s ...' % (target, site, path), logger, verbose=verbose)

                # it's at this point that this code starts modifying what's there so the lock file should
                # not be removed on failure from here on (until it succeeds)
                clean_lock = False
                
                # remove any existing measures readme.txt now in case something goes wrong during extraction
                readme_path = os.path.join(path,'geodetic/readme.txt')
                if os.path.exists(readme_path):
                    os.remove(readme_path)

                # custom filter that incorporates 'data_filter' to watch for dangerous members of the tar file
                # this adds filtering to remove the Observatories table (unless use_astron_obs_table is True) and
                # the *.old tables that may be in the geodetic tree
                def custom_filter(member, extractionPath):
                    # member is a TarInfo instance and extractionPath is the destination path
                    # use the 'data_filter' first to deal with dangerous members
                    member = tarfile.data_filter(member, extractionPath)
                    # always exclude *.old names in geodetic
                    if (member is not None) and (re.search('geodetic',member.name) and re.search('.old',member.name)):
                        member = None
                    # the use_astron_obs_table argumen only has weight if force is True
                    if (not (force and use_astron_obs_table)) and (member is not None) and (re.search('Observatories',member.name)):
                        member = None
                    return member

                # untar the target at site to path using the custom filter, do not be verbose
                do_untar_url(site, target, path, custom_filter)

                # create a new readme.txt file
                with open(readme_path,'w') as fid:
                    # site added last to not break past readers of the measures readme
                    fid.write("# measures data populated by casaconfig\nversion : %s\ndate : %s\nsite : %s" % (target, datetime.today().strftime('%Y-%m-%d'),site))

                clean_lock = True
                print_log_messages('  ... measures data updated at %s' % path, logger, verbose=verbose)

            # closing out the do_update

        # closing out the try block

    except BadLock as exc:
        # the path is known to exist so this means that the lock file was not empty and it's not locked
        msgs = [str(exc)]
        msgs.append('The lock file at %s is not empty.' % path)
        msgs.append('A previous attempt to update path may have failed or exited prematurely.')
        msgs.append('Remove the lock file and set force to True with the desired version (default to most recent).')
        msgs.append('It may be best to completely repopulate path using pull_data and measures_update.')
        print_log_messages(msgs, logger, True)
        # reraise this
        raise

    except BadReadme as exc:
        # something is wrong in the readme after an update was triggered, this shouldn't happen, print more context and reraise this
        msgs = [str(exc)]
        msgs.append('This should not happen unless multiple sessions are trying to update data at the same time and one experienced problems or was done out of sequence')
        msgs.append('Check for other updates in progress or choose a different path or clear out this path and reinstall the casarundata as well as the measures data')
        print_log_messages(msgs, logger, True)
        raise

    except RemoteError as exc:
        # probably an empty site
        msgs = [str(exc)]
        msgs.append('There was a remote error while attempting to update measures at %s' % path)
        msgs.append('Check the value of measures_site and try again')
        print_log_messages(msgs, logger, True)
        raise
        
    except Exception as exc:
        msgs = []
        msgs.append("ERROR! : Unexpected exception while updating measures at %s" % path)
        msgs.append("ERROR! : %s" % exc)
        print_log_messages(msgs, logger, True)
        raise

    finally:
        # make sure the lock file is closed and also clean the lock file if safe to do so, this is always executed
        if lock_fd is not None and not lock_fd.closed:
            if clean_lock:
                lock_fd.truncate(0)
            lock_fd.close()

    return
