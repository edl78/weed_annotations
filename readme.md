# Annotation data visualization

## Overview
- The main functionality of weed annotations is to interface CVAT and MongDB but also to present statistics regarding the annotations. MongoDB is later used in the training code.
- CVAT annotations are fetched via http api
- Annotations are fed into a Mongo Database
- MongoExpress can view the database via a browser
- Python with Dash and Plotly takes data from MongoDB and builds statistics to show on a Dashboard
- The dashboard on localhost:8050 has three buttons and a free text field: 
- "update annotations" check for new annotations set to status complete in cvat and updates the mongodb with these. This produces the statistics displayed under the buttons when complete.
- "calc t-sne, will take a long time to perform" will call the analytics service and make t-sne plots for every annotation task in the mongodb, one plot with dots and one with overlayed bbox images.
- The free text field and the associated button "calc t-sne on input field task, will take a long time to perform" will send a request to perform t-sne on the task given in the input text field.



![](doc_img/architecture.png)

### Build
- Run `sh build_stats.sh` to build the required image.

### Run
- Make a folder for mongodb to store the database and set `MONGODB_VOLUME=` your absolute path in the `.env` file (no trailing `/`). Set full permissions on the folder.
- Fill in your usernames and passwords in the env.list file for CVAT, MongoDB and ME_CONFIG. Do not check this or the `.env` file which is used by docker-compose in to git.
- Fill in all other environment variables needed, see examples below.
- Start the Analytics docker-compose if that service is desired, see the analytics repo for information. In weed_annotations env.list file: Set ANALYTICS_HOST variable to the IP of the host running the service. Leave the ANALYTICS_HOST blank if not using the analytics service. That prevents the weed_annotations application from trying to communicate with the Analytics server.
- Run `docker-compose up -d` in the weed_annotations root folder to start the application and `docker-compose down` to end.

#### Example env.list
```
CVAT_USERNAME=autoannotation
CVAT_PASSWORD=glassarfulltavsocker
CVAT_BASE_URL=http://172.16.1.20:8080/api/v1/
MONGODB_PORT_NUMBER=27017
#MONGODB_ROOT_USER=
MONGODB_ROOT_PASSWORD=mongobongoadminpass
MONGODB_USERNAME=mongobongo
MONGODB_PASSWORD=mongobongopasswd
MONGODB_DATABASE=annotations
ME_CONFIG_MONGODB_ADMINUSERNAME=root
ME_CONFIG_MONGODB_ADMINPASSWORD=mongobongoadminpass
ME_CONFIG_BASICAUTH_USERNAME=mongobongo
ME_CONFIG_BASICAUTH_PASSWORD=mongobongopasswd
ME_CONFIG_MONGODB_PORT=27017
ANALYTICS_HOST=
ANALYTICS_PORT=5001
```
If not using the analytics service, leave the `ANALYTICS_HOST=` empty as above. Otherwise set to e.g. `ANALYTICS_HOST=http://<IPNUMBER>`.


#### Example .env
```
#set variables for docker-compose
MONGODB_PORT_NUMBER=27017
MONGODB_VOLUME=/home/<YOURUSERNAME>/dev/github
STATS_PORT_NUMBER=8050
```

### Access 
- on localhost:8050 the statistics Dashboard can be viewed.
- on localhost:8081 the MongoExpress can be accessed

### Backup annotations
- If desired mongo express web gui can be used to backup annotations by downloading the information. 

### Analytics
- The analytics funtionality is handled by the analytics container which is a flask server with a http rest api. The Dashboard implements communication with the flask server and collects the results from initialized t-sne calculations when it updates its annotations. There is one button for annotation update and another for initializing t-sne analysis.
- First one has to click update annotations to populate the mongo database. The contents of the database control what is presented on the Dashboard and what analysis is performed in the analytics container.
- With the analytics service running and t-sne analysis performed, the weed_annotations dashboard can present this information as two images per task, one image with colored dots and another with overlayed bounding boxes. This will give information on feature space distribution in the task.

### Sample of statistics Dashboard

![](doc_img/Dash.png)
