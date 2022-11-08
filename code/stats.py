from pymongo import MongoClient
import pprint
import requests
import os

class Stats():
    def __init__(self):
        self.db_client = MongoClient(host='mongodb', port=27018, 
                                    username=os.environ['MONGODB_USERNAME'], password=os.environ['MONGODB_PASSWORD'],
                                    connect=True, authSource="annotations")  

        self.db = self.db_client['annotations']


    def list_tasks(self):
        pipeline = [
            { '$group': { '_id': "$name", "name": { '$sum': 1 } } },
            { '$project': { 'name': 0 } }
        ]
        output = self.db.tasks.aggregate(pipeline)
        return list(output)


    def count_num_object_classes(self):
        pipeline = [
            {'$sortByCount': "$object_class"}
        ]
        output = self.db.annotation_data.aggregate(pipeline)
        return list(output)

    def get_num_object_classes_filtered_on_task(self, name):
        pipeline = [        
                { '$match': { "task_name": name } },
                {'$sortByCount': "$object_class"}            
        ]
        output = self.db.annotation_data.aggregate(pipeline)
        return list(output)


    def get_num_per_annotation_type(self):
        pipeline = [
            {'$sortByCount': "$shape_type"}
        ]
        output = self.db.annotation_data.aggregate(pipeline)
        return list(output)