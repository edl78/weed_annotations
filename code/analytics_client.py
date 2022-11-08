import requests
import os

class AnalyticsClient():
    def __init__(self, host, port):
        self.port = port
        self.host = host
        self.base_url = self.host + ':' + str(self.port)


    def tsne_calc(self, task_name):
        endpoint = '/' + task_name.replace(' ', '_') + '/run_tsne'
        r = requests.get(self.base_url+endpoint)        
        if(r.status_code == 200):
            print('t-sne calc request ok, results at different endpoint')
        else:
            print('Error: endpoint :' + endpoint + ' reason: ' + r.reason  + 'task_name: ' + task_name)

    def download_img(self, task_name, img_name, save_path):
        endpoint = '/tsne/' + task_name.replace(' ', '_') + '/' + img_name
        r = requests.get(self.base_url+endpoint)        
        if(r.status_code == 200):
            print('write tsne plot to file for ' + task_name)
            os.makedirs(name=save_path, mode=0o755, exist_ok=True)
            with open(save_path+'/'+img_name, 'wb') as out_file:
                out_file.write(r.content)

        else:
            print('Error: endpoint :' + endpoint + ' reason: ' + r.reason  + 'task_name: ' + task_name)