import ee 
import re
from datetime import datetime
from utils import parse_date
import pandas as pd

def get_op_list( project_id):
    project_id = project_id
    initialize(project_id)
    op_list = search_ee_operations(project_id)
    op_list = [operation_from_dict(op) for op in op_list]
    data = [op.get_op_values() for op in op_list]
    return  data


class EEtaskGroup(pd.DataFrame):
    
    default_columns = ['task_name', 'task_id', 'task_description','status', 'destination_uri','destination_id', 'task_type', 'create_time', 'update_time', 'start_time', 'end_time']
    
    def __init__(self, project_id:str = None, op_list:list = None):
        if project_id:
            data = get_op_list(project_id)

        super().__init__( data, columns = self.default_columns)

    def get_completed_taks(self):
        return self.loc[self['status']=='SUCCEEDED'].copy()
    
    def get_cancelled_taks(self):
        return self.loc[self['status']=='CANCELLED'].copy()
    
    def filter_by_date(self,date_column:str, initial_date:str, end_date:str, inclusive=False):
        if initial_date:
            cutoff = pd.to_datetime(initial_date, dayfirst=True, errors='raise')
            mask = (self[date_column] >= cutoff) if inclusive else (self[date_column] > cutoff)
            return self.loc[mask].copy()
        
    def get_from_date(self,date_column:str, date_str:str):
        cutoff = pd.to_datetime(date_str, dayfirst=True, errors='raise')
        mask = self[date_column] == cutoff
        return self.loc[mask].copy()

    


class EETaskOperation():
    def __init__(self, name:str, status:str, destination:str, type:str, task_description:str, create_time:str, start_time:str, update_time:str, end_time:str):
        self.op_name = name
        self.task_id = self.op_name.split('/')[-1]
        self.status = status
        self.destination_uri = destination
        self.type = type
        self.create_time = parse_date(create_time)
        self.update_time = parse_date(update_time)
        self.start_time = parse_date(start_time)
        self.end_time = parse_date(end_time)
        self.task_description = task_description
    

    def __str__(self):
        pass

    def get_op_values(self):
        return [self.op_name, 
                self.task_id,
                self.task_description,
                self.status,
                self.destination_uri,
                self.get_destination_drive_id(),
                self.type,
                self.create_time,
                self.create_time,
                self.start_time,
                self.end_time]
    
    def get_destination_drive_id(self):
        uris = self.destination_uri
        if isinstance(uris, list):
            match = [re.search(r'https://drive.google.com/#folders/([a-zA-Z0-9_-]+)', uri) for uri in uris][0]
            if match:
                return match.group(1)
        elif isinstance(uris, str):
            match = re.search(r'https://drive.google.com/#folders/([a-zA-Z0-9_-]+)', uris)
            if match:
                return match.group(1)
        else:
            return None
        #if match:
        #    return match.group(1)
        #else:
        #    return None


def initialize(project_id:str) -> None:

    ee.Authenticate()
    ee.Initialize(project=project_id)


def operation_from_dict(op_dict):
    name=  op_dict['name']
    metadata = op_dict['metadata']

    status = metadata['state']
    description = metadata['description']
    creation_time = metadata['createTime']
    update_time = metadata['updateTime']
    start_time = metadata['startTime']
    end_time =  metadata.get('end_time')
    task_type = metadata['type']
    destination_uri =  metadata.get('destinationUris')




    return EETaskOperation(name=name, 
                           status=status,
                           destination=destination_uri,
                           type=task_type,
                           create_time=creation_time,
                           start_time=start_time,
                           end_time=end_time,
                           update_time=update_time,
                           task_description = description

    )


def search_ee_operations(project_id, status=None, creation_date=None, start_date=None, end_date=None, type=None, task_id=None):
    initialize(project_id)
    ops = ee.data.listOperations()
    if status:
        ops  = [ op for op in ops if op['metadata']['state'] == status]
    if start_date:
        ops  = [ op for op in ops if parse_date(op['metadata']['startTime']) == parse_date(start_date)]
    if end_date:
        ops  = [ op for op in ops if parse_date(op['metadata']['endTime']) == parse_date(end_date)]
    if creation_date:
        ops  = [ op for op in ops if parse_date(op['metadata']['createTime']) == parse_date(creation_date)]
    if type:
        ops  = [ op for op in ops if op['metadata']['type'] == type]
    if task_id:
        ops  = [ op for op in ops if op['name'] in task_id]
    return ops 

if __name__ == "__main__":
    ops = EEtaskGroup(project_id='conab-crop-mapping')
    
    #print(ops.columns)
    cancelled = ops.get_cancelled_taks()
    cancelled.to_csv('tasks_cancelled.csv', index=False)
    # print(type(cancelled))
    # filtred_cancelled = cancelled.get_from_date('create_date','03-09-2025')
    # print(filtred_cancelled.head())
    #ops = search_ee_operations(status='SUCCEEDED',creation_date='2025-08-28',project_id='conab-crop-mapping')
    # print(len(ops))
    # print(ops[0])
    # print(ops[0].keys())
    #uris = (ops[0]['metadata']['destinationUris'])
    #match = [re.search(r'https://drive.google.com/#folders/([a-zA-Z0-9_-]+)', uri) for uri in uris][0].group(1)
    #print(match)
