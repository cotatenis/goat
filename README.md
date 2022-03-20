
░█████╗░░█████╗░████████╗░█████╗░████████╗███████╗███╗░░██╗██╗░██████╗
██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗╚══██╔══╝██╔════╝████╗░██║██║██╔════╝
██║░░╚═╝██║░░██║░░░██║░░░███████║░░░██║░░░█████╗░░██╔██╗██║██║╚█████╗░
██║░░██╗██║░░██║░░░██║░░░██╔══██║░░░██║░░░██╔══╝░░██║╚████║██║░╚═══██╗
╚█████╔╝╚█████╔╝░░░██║░░░██║░░██║░░░██║░░░███████╗██║░╚███║██║██████╔╝
░╚════╝░░╚════╝░░░░╚═╝░░░╚═╝░░╚═╝░░░╚═╝░░░╚══════╝╚═╝░░╚══╝╚═╝╚═════╝░


--------------------------------------------------------------------------

# Web crawler

url: [https://www.goat.com/](https://www.goat.com/)

- Our spiders will collect data from the `timeline` section in the GOAT website: https://www.goat.com/timeline. Thus, the parameters should be think to collect certains years of that timeline. For instance, for 2021 year our endpoint will be that https://www.goat.com/timeline/2021.

# 1. Configuration
Before you run this project and for the proper running of this program you need to set up some variables inside `goat/goat/settings.py`.

## 1.1 SENTRY
This project utilizes [SENTRY](https://sentry.io/) for error tracking.

- `SPIDERMON_SENTRY_DSN`
- `SPIDERMON_SENTRY_PROJECT_NAME`
- `SPIDERMON_SENTRY_ENVIRONMENT_TYPE`

## 1.2 GOOGLE CLOUD PLATFORM

- `GCS_PROJECT_ID` 
- `GCP_CREDENTIALS`
- `GCP_STORAGE`
- `GCP_STORAGE_CRAWLER_STATS`
- `IMAGES_STORE`

## 1.3 DISCORD
- `DISCORD_WEBHOOK_URL`
- `DISCORD_THUMBNAIL_URL`
- `SPIDERMON_DISCORD_WEBHOOK_URL`

# 2. Build

```shell
cd goat
make docker-build-production
```
# 3. Publish

```shell
make docker-publish-production
```

# 4. Use
- The parameter `brand` could receive one of the following values: [`adidas`, `adidas-yeezy`, `air-jordan`, `nike`].

```shell
docker run --shm-size="2g" gcr.io/cotatenis/cotatenis-crawl-goat:0.2.2 --brand=adidas --years=2021,2020
```
