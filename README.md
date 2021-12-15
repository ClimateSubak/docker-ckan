# CKAN setup for Subak's Data Cooperative

Taking as a starting point the [CKAN-in-docker repository](https://github.com/okfn/docker-ckan) by the Open Knowledge Foundation, the original README and setup instructions can now be found in [SETUP.md](/SETUP.md).

## Local / staging / prod
Local using docker-desktop (for example).   
Staging and prod on AWS Elastic Container Service (ECS) so we can use the same dockerfiles.
Deploy to staging: XXX  
Deploy to prod: XXX  

## Developing locally
`cp .env.example .env`  
`docker-compose build`  
`docker-compose run`  

For staging and production:  
environment variables will be set in EKS.

## Deploying to ECS
Following [this tutorial](https://aws.amazon.com/blogs/containers/deploy-applications-on-amazon-ecs-using-docker-compose/).  

Images can be hosted in our private container registry on AWS: `848094190915.dkr.ecr.us-east-1.amazonaws.com/subak-datacatalogue`. 
Log in with docker to our registry:   
`aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 848094190915.dkr.ecr.us-east-1.amazonaws.com`

Tag and push our images to the registry - ckan, db, datapusher, solr (redis is standard image) using script `ecs_push_images.sh`
Only new image layers will be pushed.  

Now we can use the `docker-compose.ecs.yml` file to deploy to the `subakecscontext` Docker context, which points to the image repository.

## Adding plugins
Update the CKAN Dockerfile with the plugins desired and add to the CKAN_PLUGINS section in the `.env` file. Extra config like db updates may need to be done in a docker entryfile or similar.

Rebuild any one container by specifying the service name: `docker-compose build ckan`  
Then `docker-compose up` to recreate again.

Extensions added:  pages, dcat, harvester, scheming (datasets for now)

## Sysadmin
Basic tasks have been done in the `prerun.py` file and other commands can be added to the `start_ckan.sh` entrypoint file under `ckan-base/2.9/setup/start_ckan.sh`  

### Executing CKAN commands
`docker-compose -f docker-compose.yml exec ckan /bin/bash -c "ckan <YOUR COMMAND>"`  
`docker-compose -f docker-compose.yml exec ckan /bin/bash -c "ckan sysadmin add ckan_admin"`


## Basic customisation
Make basic changes with the UI at "http://<my-ckan-url>/ckan-admin/config/"  
Site Title: Subak Data Catalogue  
Style: Default  
Site Tag Line: Share the data, save the planet  
Site logo: https://images.squarespace-cdn.com/content/v1/5fbe3c75a5bc066edf9513f2/1606745984909-KHIUHFOBXP5NTTNVMG5B/SUBAK_LOGO.png  
 About:  
 Intro Text:  
 Custom CSS:  
 Homepage: Search, introductory area and stats  
 
