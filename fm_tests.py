"""
FMP19 Connector
"""

# %% import libraries
#from fmrest import dataAPI
from fmrest import server
import os
import json
import re
# %% define functions



def pull_the_table(
    credentials,
    database,
    layout,
    table_keys
):
    SERVER_IP = credentials['ip']
    USER = credentials['user']
    PASSWORD = credentials['password']
    DATABASE = database
    LAYOUT = layout

    fms =  server.Server(
        SERVER_IP,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        layout=LAYOUT,
        api_version="v2",
        verify_ssl=False
    )

    records = []
    offset = 0
    limit = 100
    fms.login()

    while True:
        try:
            print(f'{offset}-{len(records)}')
            if offset == 0:
                current_records = fms.get_records() 
            else:
                current_records = fms.get_records(offset=offset)
            records+=[i for i in current_records]
            offset += limit
            if not current_records.is_complete: break

        except Exception as e:
            print(e)
            break
        
    fms.logout()


    record_dict = {
        i['recordId']:{
            k:i[k] for k in table_keys 
        } for i in records
    }
    return record_dict

# %%
def pull_specific_record(
    credentials,
    database,
    layout,
    search_args,
    table_keys
):
    SERVER_IP = credentials['ip']
    USER = credentials['user']
    PASSWORD = credentials['password']
    DATABASE = database
    LAYOUT = layout

    fms =  server.Server(
        SERVER_IP,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        layout=LAYOUT,
        api_version="v2",
        verify_ssl=False
    )

    fms.login()

    records = fms.find([search_args])

    fms.logout()
    record_dict = {
        i['recordId']:{
            k:i[k] for k in table_keys 
        } for i in records
    }

    # need warning if multiple keys in dict

    return record_dict[list(record_dict.keys())[0]]


# %%

def extract_ruid(
        filename
        ):
    """
    Extracts ruid information from a filename

    Parameters
    ----------
    filename : string
        filename, expected as MUID_PLYUID.txt format


    Returns
    -------
    ruid : string

    """
    
    ruid_re = re.compile(
        '(?i)^((?P<plyuid>Ply[^_^.^-]*)|(?P<ruid>R[^_^.^-]*)|(?P<muid>M[^_^.^-]*)|(?P<pmid>PM[^_^.^-]*)|(_?.*?_?))+(_.*)*.*$'
    )
    return ruid_re.match(filename).group('ruid')


def generate_rig_save_path(filename):
        #%%
    with open('/home/pi/rig.config','r') as openfile:
        config = json.load(openfile)
        

    table_keys = [
        'PlyUID',
        'RUID',
        'Project Number'
    ]

    credentials = {
        'ip':config['SERVER_IP'],
        'user':config['USER'],
        'password':config['PASSWORD']
    }
        
    # %%
    
    ruid = extract_ruid(filename)
    query_dict = pull_specific_record(
        credentials, 
        config["DATABASE"], 
        config["LAYOUT"],
        {'RUID':ruid},
        table_keys
    )

    rigname = config["RIGNAME"]

    filepath = os.path.join(
        "/media/pi",
        rigname,
        query_dict["Project Number"],
        filename+".txt"
    )
    
    return filepath

# %% define main()
def main():

    
    # %%
    ruid_plyuid_pmid = input("RUID_PlyUID_PMID:\n")
    print(generate_rig_save_path(ruid_plyuid_pmid))
    

    #%%
# %% run main
if __name__ == "__main__":
    main()
