#!/usr/bin/python

"""
Creators GET API interface v0.3.2
Full API docs: http://get.creators.com/docs/wiki
@author Brandon Telle <btelle@creators.com>
@copyright (c) 2015 Creators <www.creators.com>
"""

import subprocess, shlex, re, urllib, os.path

# Python 3+ puts urlencode in urllib.parse
try:
    from urllib import parse
    use_parse = True
except:
    use_parse = False
    
# We need some way to parse JSON responses
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        raise ImportError("A JSON library is required to use Creators_API")
 
# Try to use pycURL instead of system calls
try:
    import pycurl
    from io import BytesIO
    use_pycurl = True
except ImportError:
    use_pycurl = False

# User's API Key
api_key = ""

# API url
api_url = "http://get.creators.com/"

# API version
api_version = 0.32

# API key length
api_key_length = 40

# Make an API request
# @param endpoint string API url
# @param parse_json bool if True, parse the result as JSOn and return the parsed object
# @throws ApiError if an error code is returned by the API
# @return parsed JSON object, or raw return string
def __api_request(endpoint, parse_json=True, post_data={}, destination=''):
    if api_key == "" and len(post_data) == 0:
        raise ApiError('API key must be set')
    
    data = ''
    if len(post_data) > 0:
        try:
            data = urllib.urlencode(post_data)
        except:
            try:
                data = urllib.parse.urlencode(post_data)
            except:
                raise ApiError('Cannot parse post string')
    
    if use_pycurl:
        c = pycurl.Curl()
        c.setopt(c.URL, api_url+endpoint)
        
        if data != '':
            c.setopt(c.POSTFIELDS, data)
        
        c.setopt(c.HTTPHEADER, ['X_API_KEY: '+api_key, 'X_API_VERSION: '+str(api_version)])
        c.setopt(c.FOLLOWLOCATION, True)
        
        buffer = BytesIO()
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()
        ret = buffer.getvalue()
        
        try:
            ret = ret.decode('UTF-8')
        except:
            if destination != '':
                f = open(destination, 'wb')
                f.write(ret)
                f.close()
                ret = True
            else:
                raise ApiError('Cannot parse API response')
        
    else:    
        cmd = 'curl --silent -L --header "X_API_KEY: '+api_key+\
                '" --header "X_API_VERSION: '+str(api_version)+'" '
        
        if data != '':
            cmd += '-X POST --data "'+data+'" '
            
        cmd += api_url+endpoint
        
        ret = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE).stdout.read()
    
    # Check for HTTP error messages
    if type(ret) is str:
        err = re.search('Error ([0-9]+): (.*)', ret)
        if err != None:
            raise ApiError(err.group(2), err.group(1))
    
    # Parse JSON if required
    if parse_json:
        try:
            ret = json.loads(ret)
        except:
            pass
        
    # Check for API-generated error messages, throw exception
    try:
        if type(ret) is dict and ret['error'] > 0:
            raise ApiError(ret['message'], ret['error'])
    
    except KeyError:
        pass
    
    return ret

def authenticate(username, password):
    try:
        login = {'username':username, 'password':password}
        ret = __api_request('api/users/auth', post_data=login)
    except:
        return False
    
    if type(ret) is dict and type(ret['api_key']) is str and len(ret['api_key']) == api_key_length:
        global api_key
        api_key = ret['api_key']
        return True
        
    return False
    
# SYN the server
# @return string "ack"
def syn():
    return __api_request('api/etc/syn')
    
# Get a list of available active features
# @param limit int number of results to return
# @param get_all bool if true, results will include inactive features
# @return list of features
def get_features(limit=1000, get_all=False):
    return __api_request('api/features/get_list/json/NULL/'+str(limit)+'/0?get_all='+str(int(get_all)))

# Get details on a feature
# @param filecode string unique filecode for the feature
# @return dict feature info
def get_feature_details(filecode):
    return __api_request('api/features/details/json/'+str(filecode))
    
# Get a list of releases for a feature
# @param filecode string unique filecode for a feature
# @param offset int offset, default 0
# @param limit int limit, default 10
# @param start_date string start date: YYYY-MM-DD, default none
# @param end_date string end_date: YYYY-MM-DD, default none
# @return list of releases
def get_releases(filecode, offset=0, limit=10, start_date='', end_date=''):
    return __api_request('api/features/get_list/json/'+str(filecode)+"/"+str(limit)+"/"+str(offset)+"?start_date="+str(start_date)+"&end_date="+str(end_date))
    
# Download a file
# @param url string URL string provided in the files section of a release result
# @param destination string path to the location the file should be saved to
# @throws ApiError if destination is not a writable file location or url is unavailable
# @return bool True if file is downloaded successfully
def download_file(url, destination):
    if not os.path.isdir(destination):
        try:
            contents = __api_request(url, parse_json=False, destination=destination)
            
            if type(contents) is bool:
                return contents
            
            f = open(destination, 'wb')
            if len(contents) and contents[0] == '{':                     # Poor man's JSON check
                contents = json.loads(contents)
                try:
                    if type(contents) is dict and contents['error'] > 0:
                        f.close()
                        raise ApiError(contents['message'], contents['error'])
                
                except:
                    f.close()
                    raise ApiError("Unexpected content type: JSON")

            f.write(contents)
            f.close()
            return True
        except IOError:
            raise ApiError("Destination is unavailable or unwriteable")
        except ApiError:
            raise
    else:
        raise ApiError("Destination is a directory")
    
# Download a zip archive of the entire contents of a release
# @param release_id int the unique ID of the release to download
# @param destination string path to the location the file should be saved to
# @throws ApiError if destination is not a writeable file or release is not found
# @return bool True if file is downloaded successfully
def download_zip(release_id, destination):
    if not os.path.isdir(destination):
        try:
            contents = __api_request('/api/files/zip/'+str(release_id), parse_json=False, destination=destination)
            if type(contents) is bool:
                return contents
            
            f = open(destination, 'w')
            
            if len(contents) > 0 and contents[0] == '{':                     # Poor man's JSON check
                contents = json.loads(contents)
                try:
                    if type(contents) is dict and contents['error'] > 0:
                        f.close()
                        raise ApiError(contents['message'], contents['error'])
                
                except:
                    f.close()
                    raise ApiError("Unexpected content type: JSON")
            
            f.write(contents)
            f.close()
            return True
        except IOError:
            raise ApiError("Destination is unavailable or unwriteable")
        except ApiError:
            raise
    else:
        raise ApiError("Destination is a directory")
    

# API Exception class
class ApiError(Exception):
    def __init__(self, value, errno=0):
        self.value = value
        self.errno = errno
        
    def __str__(self):
        val = ''
        if self.errno > 0:
            val += '[Errno '+str(self.errno)+'] '
        val += self.value
        return repr(val)