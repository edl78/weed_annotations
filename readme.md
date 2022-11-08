# Annotation data visualization

## Overview
- The main functionality of weed annotations is to interface CVAT and MongDB but also to present statistics regarding the annotations. MongoDB is later used in the training code.
- CVAT annotations are fetched via http api
- Annotations are fed into a Mongo Database
- MongoExpress can view the database via a browser
- Python with Dash and Plotly takes data from MongoDB and builds statistics to show on a Dashboard



![](doc_img/architecture.png)

### Build
- Run `sh build_all.sh` to build all images required

### Run
- First fill in your usernames and passwords in the env.list file. Do not check this in.
- Run `docker-compose up -d` to start the application and `docker-compose down` to end

### Access 
- on localhost:8050 the statistics Dashboard can be viewed.
- on localhost:8081 the MongoExpress can be accessed
- Mongo Compass is easiest to run natively on the host and can be downloaded here: https://www.mongodb.com/try/download/compass

### Backup annotations
- in the cvat_com.py the main function implements a backup functionality. There is a run_backup.sh script that starts a Docker container and extracts all task annotation data from cvat and stores the data on a given path. Task meta data is stored in a json file and annotations are stored in three different formats: CVAT 1.1, COCO 1.0 and PASCAL VOC 1.1
- the cvat_com.py accepts flags: --backup=bool --filepath=path_to_store_backup (can add several of these if desired and we use this to backup on two different NAS devices)
- the backup functionality is extended from previous cvat http api communication implementation so the container can use the same image as stats:v1 already in use for other purposes

### Analytics
- The analytics funtionality is handled by the analytics container which is a flask server with a http rest api. The Dashboard implements communication with the flask server and collects the results from initialized t-sne calculations when it updates its annotations. There is one button for annotation update and another for initializing t-sne analysis.
- First one has to click update annotations to populate the mongo database. The contents of the database control what is presented on the Dashboard and what analysis is performed in the analytics container.

### Sample of statistics Dashboard

![](doc_img/Dash.png)
