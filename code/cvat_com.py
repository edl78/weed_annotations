import requests
from pymongo import MongoClient
import time
import argparse
import os
from datetime import datetime
import json

class Annotations():
    def __init__(self, username, password, cvat_base_url, backup=False):
        self.cvat = cvat_base_url
        self.username = username
        self.password = password
        self.auth_token = None
        self.cookies = None
        self.tasks = dict()
        if(not backup):     
            self.db_client = MongoClient(host='mongodb', port=27018, 
                                username=os.environ['MONGODB_USERNAME'], password=os.environ['MONGODB_PASSWORD'],
                                connect=True, authSource="annotations")

            self.db = self.db_client['annotations']
            self.db_collection_tasks = self.db.tasks
            self.db_collection_annotation_data = self.db.annotation_data
            self.db_collection_task_meta = self.db.meta

    def get_tasks(self):
        endpoint = 'tasks'
        #get first list of tasks
        r = requests.get(self.cvat+endpoint, cookies=self.cookies)
        if(r.status_code == 200):
            #tasks is a paginated list of tasks
            task_list = r.json()
            for task in task_list['results']:
                if(task['status'] == 'completed'):
                    self.tasks[task['name']] = task
            #get all other lists of tasks
            while(task_list['next'] is not None):
                #get all pages, build the list
                r = requests.get(task_list['next'], cookies=self.cookies)
                task_list = r.json()
                if(r.status_code == 200):
                    for task in task_list['results']:
                        if(task['status'] == 'completed'):
                            self.tasks[task['name']] = task
                else:
                    print(r.reason)                    
        else:
            print(r.reason)


    def login(self):
        endpoint = 'auth/login'
        body = {'username': self.username, 'password': self.password}
        print('cvat auth in progress')
        r = requests.post(self.cvat+endpoint, data = body, timeout=30)
        if(r.status_code == 200):
            self.cookies = r.cookies
            print('cvat auth done')
        else:
            print(r.reason)
            print('cvat auth failed')
    

    def get_annotation(self, task_name):
        endpoint = 'tasks/' + str(self.tasks[task_name]['id']) + '/annotations'
        r = requests.get(self.cvat+endpoint, cookies=self.cookies)
        annotation = None
        if(r.status_code == 200):
            annotation = r.json()
            #create binding to task_data info
            annotation.update({'task_name': task_name})
        else:
            print('Error: endpoint :' + endpoint + ' reason: ' + r.reason  + 'task_name: ' + task_name)

        return annotation


    def download_annotation(self, task_name, format, filename):
        endpoint = 'tasks/' + str(self.tasks[task_name]['id']) + '/annotations'
        body = {'format': format, 'filename': filename, 'action': 'download'}
        r = requests.get(self.cvat+endpoint, cookies=self.cookies, data=body)        
        text = ""
        if(r.status_code == 200):
            text = r.json()
            print('downloaded: ' + filename)
        else:
            print('Error: endpoint :' + endpoint + ' reason: ' + r.reason  + 'task_name: ' + task_name)
        return text


    def get_label(self, labels, id):
        for label in labels:
            if(label['id'] == id):
                return label['name']
        return None
    

    def populate_db_with_task(self, task):
        post = {
            'type': 'task_data',
            'name': task['name'],
            'labels': task['labels'],
            'created_date': task['created_date'],
            'updated_date': task['updated_date']
        }
        self.db_collection_tasks.insert_one(post)


    def get_meta_data(self, task_name):        
        endpoint = 'tasks/' + str(self.tasks[task_name]['id']) + '/data/meta'
        r = requests.get(self.cvat+endpoint, cookies=self.cookies)
        meta_data = None
        if(r.status_code == 200):
            meta_data = r.json()            
        else:
            print('Error: endpoint :' + endpoint + ' reason: ' + r.reason  + 'task_name: ' + task_name)

        return meta_data

    
    def populate_db_with_meta(self, task_name):
        meta = self.get_meta_data(task_name)
        post = {
            'task_name': task_name,
            'frames': meta['frames']
        }
        self.db_collection_task_meta.insert_one(post)


    def remove_meta_from_db(self, task_name):
        self.db_collection_task_meta.delete_one({'task_name': task_name})


    def populate_db_with_annotations(self, task_name):    
        labels = self.tasks[task_name]['labels']
        annotation = self.get_annotation(task_name)
        #iterate over all shapes (actual annotations)
        meta_data = self.get_meta_data(task_name)
        for shape in annotation['shapes']:
            meta = meta_data['frames'][int(shape['frame'])]            
            post = {
                'type': 'annotation',
                'task_name': annotation['task_name'],
                'shape_type': shape['type'],
                'occluded': shape['occluded'],
                'points': shape['points'],
                'frame': shape['frame'],
                'label_id': shape['label_id'],
                'source': shape['source'],
                'object_class': self.get_label(labels, shape['label_id']),
                'img_path': meta['name'],
                'img_height': meta['height'],
                'img_width': meta['width']
            }
            self.db_collection_annotation_data.insert_one(post)


    def remove_annotations_from_db(self, task_name):
        del_query = { "task_name": {"$regex": "^" + task_name} }
        self.db_collection_annotation_data.delete_many(del_query)

    
    def remove_task_from_db(self, task_name):
        self.db_collection_tasks.delete_one({'name': task_name})


    def get_db_tasks(self):
        db_tasks = {}
        for task_name in self.tasks.keys():            
            res = self.db_collection_tasks.find_one({'name': task_name})
            db_tasks[task_name] = res
            
        return db_tasks


    def startup(self):        
        self.login()

    def get_formats(self):
        endpoint = '/server/annotation/formats'                   
        r = requests.get(self.cvat+endpoint, cookies=self.cookies)
        formats = None
        if(r.status_code == 200):
            formats = r.json()
        else:
            print('Error: endpoint :' + endpoint + ' reason: ' + r.reason)

        return formats


    def backup(self, filepath):
        self.tasks.clear()
        self.get_tasks()
        #formats = self.get_formats()
        formats_short = [{'name': 'CVAT 1.1', 'ext': 'ZIP'}, {'name': 'COCO 1.0', 'ext': 'ZIP'}, {'name': 'PASCAL VOC 1.1', 'ext': 'ZIP'}]
        for task_name in self.tasks.keys():
            print('backup ' + task_name)
            folderpath = filepath + task_name + '/'
            os.makedirs(name=folderpath, mode=0o755, exist_ok=False)
            task_meta = self.get_meta_data(task_name)
            taskpath = folderpath + 'task_meta_data' + '.json'
            with open(taskpath, 'w') as f:
                json.dump(task_meta, f, ensure_ascii=False)

            for format in formats_short:
                text = self.download_annotation(task_name=task_name, format=format['name'], filename=format['name'] + '.' + format['ext'])
                fullpath = folderpath + format['name'] + '.' + format['ext']
                with open(fullpath, 'w') as f:
                    json.dump(text, f, ensure_ascii=False)

   
        
    def update(self):
        #implement semi intelligent update of annotations
        #add missing or updated annotations, in case of update
        #remove old and insert new.
        self.tasks.clear()
        self.get_tasks()
        db_tasks = self.get_db_tasks()
        for task_name in self.tasks.keys():
            print(task_name + ' start handling')
            if(db_tasks[task_name] == None):
                #just add
                self.populate_db_with_meta(task_name)
                self.populate_db_with_task(self.tasks[task_name])
                self.populate_db_with_annotations(task_name)
                print(task_name + ' annotations added')
            else:
                #update existing, check date
                if(self.tasks[task_name]['updated_date'] > db_tasks[task_name]['updated_date']):
                    #newer, update
                    print(task_name + ' handle update')
                    self.remove_task_from_db(task_name)
                    self.populate_db_with_task(self.tasks[task_name])
                    self.remove_meta_from_db(task_name)
                    self.populate_db_with_meta(task_name)
                    self.remove_annotations_from_db(task_name)
                    self.populate_db_with_annotations(task_name)
                    print(task_name + ' update finished')
                else:
                    print(task_name + ' already updated')
            print(task_name + ' all done')

def main():    
    parser = argparse.ArgumentParser(description='CVAT commuication module, can be used for backup')
    parser.add_argument('-b', '--backup', type=bool, default=False, help='bool for backup functionality')
    parser.add_argument('-f', '--filepath', action='append', help='filepath where to save backup, ok to stack several flags', required=False)
    args = parser.parse_args()

    #get user, pass and base_url from env later, ok for now.
    annotations = Annotations(username=os.environ['CVAT_USERNAME'], 
                            password=os.environ['CVAT_PASSWORD'],
                            cvat_base_url=os.environ['CVAT_BASE_URL'],
                            backup=args.backup)

    
    annotations.startup()


    if(args.backup):
        for f in args.filepath:
            t = datetime.now()
            datestr = t.strftime("%Y_%m_%d_%H_%M_%S")
            fullpath = f + '/' + datestr +  '/'            
            annotations.backup(filepath=fullpath)
   

    

if __name__ == "__main__":
    main()
