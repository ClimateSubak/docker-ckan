# CKAN setup for Subak's Data Cooperative

Taking as a starting point the [CKAN-in-docker repository](https://github.com/okfn/docker-ckan) by the Open Knowledge Foundation, the original README and setup instructions can now be found in [SETUP.md](/SETUP.md).

## Local / staging / prod
Docker Compose is used to manage building and running of the docker containers. 

- `docker-compose.yml` contains the build/run config for production
- `docker-compose.staging.yml` extends the production build/run config for staging
- `docker-compose.override.yml` extends the production build/run config for developing locally

The `make` commands in `Makefile` read the `ENVIRONMENT` env var in `.env` and use the correct combination of docker-compose files for each environment

## Developing locally
`cp .env.example .env`
`make build.all`  
`make up`

View logs using:

`make logs`

The CKAN web UI will now be running at `http://localhost` by default

### Local theme development
To load the subak CKAN theme for local development, first clone the [ckanext-subakdc](https://github.com/ClimateSubak/ckanext-subakdc) repo under the `/src` directory in this project. Secondly add `subakdc` as a plugin to the list of `CKAN__PLUGINS` in the `.env` file. Finally, restart the docker stack.

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
Some customisation of the CKAN web UI is not controlled within the theme, but instead by values set in the CKAN config. To make these config changes, either run the `setup_ckan_instance_config.py` script in the [ckan-scripts](https://github.com/ClimateSubak/ckan-scripts) repo, or log in to the web UI with superuser privileges at `http://<my-ckan-url>/ckan-admin/config/` and set the following fields as so:

**Site Title**: Subak Data Catalogue  
**Style**: Default  
**Site Tag Line**: Share the data, save the planet  
**Site logo**: https://images.squarespace-cdn.com/content/v1/5fbe3c75a5bc066edf9513f2/1606745984909-KHIUHFOBXP5NTTNVMG5B/SUBAK_LOGO.png  
**About**: \<contents of [ABOUT.md](https://github.com/ClimateSubak/docker-ckan/blob/main/ABOUT.md) file>  
**Intro Text**: \
**Custom CSS**: \
**Homepage**: Search, introductory area and stats  

## Plugin requirements
The dataset voting plugin enhancement requires the following command to create the db tables:  
`ckan voting initdb`

`ckan sysadmin add ckan_admin`