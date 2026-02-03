## Cloud Scheduler job setup
```shell
gcloud --project webhost-common scheduler jobs create http game-descriptor-retrain \
    --schedule "13 5 * * 2" \
    --http-method POST \
    --description "Weekly model retrain" \
    --location europe-west1 \
    --time-zone "Europe/Helsinki" \
    --max-retry-attempts 1 \
    --uri https://game-descriptor-232474345248.europe-north1.run.app/_train \
    --oidc-service-account-email job-trigger@webhost-common.iam.gserviceaccount.com \
    --oidc-token-audience https://game-descriptor-232474345248.europe-north1.run.app


# parse new content twice a day
# 01:00 and 01:10
gcloud --project webhost-common scheduler jobs create http game-descriptor-parse \
    --schedule "0-10/10 1 * * *" \
    --http-method POST \
    --description "Batch parse new description content" \
    --location europe-west1 \
    --time-zone "Europe/Helsinki" \
    --max-retry-attempts 1 \
    --min-backoff "300s" \
    --uri https://game-descriptor-232474345248.europe-north1.run.app/_parse_descriptions?batch_size=150 \
    --oidc-service-account-email job-trigger@webhost-common.iam.gserviceaccount.com \
    --oidc-token-audience https://game-descriptor-232474345248.europe-north1.run.app

gcloud --project webhost-common scheduler jobs create http game-descriptor-generate-image \
    --schedule "0 9 * * *" \
    --http-method POST \
    --description "Generate screenshot image" \
    --location europe-west1 \
    --time-zone "Europe/Helsinki" \
    --uri https://game-descriptor-232474345248.europe-north1.run.app/_generate_image \
    --oidc-service-account-email job-trigger@webhost-common.iam.gserviceaccount.com \
    --oidc-token-audience https://game-descriptor-232474345248.europe-north1.run.app
```
