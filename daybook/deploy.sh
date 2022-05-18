#!/bin/bash -e

# Set Consistent ENV vars across Travis/Buddy
# ====================================================================================

BUILD_AND_PUSH=false

if [ ! -z ${TRAVIS_COMMIT+x} ] && [ ! -z ${TRAVIS_BRANCH+x} ] && [ ! -z ${TRAVIS_JOB_WEB_URL+x} ]; then
    echo "Setting COMMIT/BRANCH from TRAVIS_COMMIT and TRAVIS_BRANCH"
    COMMIT=$TRAVIS_COMMIT
    BRANCH=$TRAVIS_BRANCH
    JOB_URL=$TRAVIS_JOB_WEB_URL
    BUILD_AND_PUSH=true
elif [ ! -z ${BUDDY_EXECUTION_REVISION+x} ] && [ ! -z ${BUDDY_EXECUTION_BRANCH+x} ] && [ ! -z ${BUDDY_EXECUTION_URL+X} ]; then
    COMMIT=$BUDDY_EXECUTION_REVISION
    BRANCH=$BUDDY_EXECUTION_BRANCH
    JOB_URL=$BUDDY_EXECUTION_URL

    # On Buddy, the APP_NAME is optional, and we can default to the repo name.
    if [ -z ${APP_NAME+x} ]; then
        APP_NAME=$BUDDY_PROJECT_NAME
    fi
elif [ -z ${COMMIT+x} ] || [ -z ${BRANCH+x} ] || [ -z ${JOB_URL+x} ]; then
    echo "COMMIT, BRANCH, or JOB_URL unset, unaable to contine "
    exit 1
fi

if [ -z ${APP_NAME+x} ]; then
    echo "No APP_NAME set, quitting"
    exit 1
fi

if [ -z ${ECR_REPO+x} ]; then
    echo "No ECR_REPO set, quitting"
    exit 1
fi

if [ -z ${IMAGE_NAME+x} ]; then
    echo "No IMAGE_NAME set, quitting"
    exit 1
fi

if [ ! -z ${AWS_REGION} ]; then
    echo "Setting AWS_DEFAULT_REGION variable from AWS_REGION"
    AWS_DEFAULT_REGION=$AWS_REGION
fi

# Post a code deployment event to New Relic's REST API
# ====================================================================================

if [ ! -z ${NEW_RELIC_APP_ID+x} ]; then
    echo "Posting New Relic Deployment Event"
    curl -X POST "https://api.newrelic.com/v2/applications/${NEW_RELIC_APP_ID}/deployments.json" \
    -H "X-Api-Key:${NEW_RELIC_REST_API_KEY}" -i \
    -H "Content-Type: application/json" \
    -d \
    "{\"deployment\":{\"revision\":\"${COMMIT}\",\"description\":\"${JOB_URL}\"}}"
else
    echo "NEW_RELIC_APP_ID undefined, skipping posting of deployment event."
fi


# Configure AWS and Login to ECR
# ====================================================================================

echo "Setting default region"
aws configure set default.region ${AWS_DEFAULT_REGION}

# Build and push Docker image
# ====================================================================================

if [ "$BUILD_AND_PUSH" = true ]; then
    echo "Log in to ECR"
    $(aws ecr get-login --no-include-email)

    # Build the image. Uses build arguments for GitHub private repo access
    echo "Building the base image with tag $ECR_REPO"
    docker build --build-arg GITHUB_TOKEN=$GITHUB_TOKEN -t ${IMAGE_NAME}:${COMMIT} .
    docker push ${IMAGE_NAME}:${COMMIT}
fi

# Tag Image on ECR
# ====================================================================================

echo "Retrieving image manifest for ${ECR_REPO}:${COMMIT}"
MANIFEST=$(aws ecr batch-get-image --repository-name ${ECR_REPO} --image-ids imageTag=${COMMIT} --query 'images[].imageManifest' --output text)
DIGEST=$(aws ecr batch-get-image --repository-name ${ECR_REPO} --image-ids imageTag=${COMMIT} --query 'images[].imageId.imageDigest' --output text)

# If the master branch was used, reference ":latest" as this change
if [ "$BRANCH" = "master" ]; then
    if [[ $(aws ecr describe-images --repository-name ${ECR_REPO} --image-ids imageDigest=${DIGEST},imageTag=latest) =~ "ImageNotFoundException" ]]; then
        echo "Tagging ${IMAGE_NAME}:${COMMIT} as ${IMAGE_NAME}:latest"
        aws ecr put-image --repository-name ${ECR_REPO} --image-tag latest --image-manifest "${MANIFEST}"
    else
        echo "Skipping tagging of ${IMAGE_NAME}:latest, already exists at ${DIGEST}"
    fi
fi

# Push new image tag per branch name
if [[ $(aws ecr describe-images --repository-name ${ECR_REPO} --image-ids imageDigest=${DIGEST},imageTag=${BRANCH}) =~ "ImageNotFoundException" ]]; then
    echo "Tagging ${IMAGE_NAME}:${COMMIT} as ${IMAGE_NAME}:$BRANCH"
    aws ecr put-image --repository-name ${ECR_REPO} --image-tag ${BRANCH} --image-manifest "${MANIFEST}"
else
    echo "Skipping tagging of ${IMAGE_NAME}:${BRANCH}, already exists at ${DIGEST}"
fi

# Push the git SHA (COMMIT) to ECR to facilitate troubleshooting
if [[ $(aws ecr describe-images --repository-name ${ECR_REPO} --image-ids imageDigest=${DIGEST},imageTag=${BRANCH}-${COMMIT}) =~ "ImageNotFoundException" ]]; then
    echo "Tagging ${IMAGE_NAME}:${COMMIT} as ${IMAGE_NAME}:${BRANCH}-${COMMIT}"
    aws ecr put-image --repository-name ${ECR_REPO} --image-tag ${BRANCH}-${COMMIT} --image-manifest "${MANIFEST}"
else
    echo "Skipping tagging of ${IMAGE_NAME}:${BRANCH}-${COMMIT}, already exists at ${DIGEST}"
fi


# Deploy to ECS
# ====================================================================================

# Create a list of services to deploy to - by default this will
# be to the $BRANCH environment and the $APP_NAME service
if [ -z ${DEPLOY_SERVICE_NAMES+x} ]; then
    DEPLOY_SERVICE_NAMES=("${APP_NAME}")
else
    IFS=',' read -r -a DEPLOY_SERVICE_NAMES <<< "$DEPLOY_SERVICE_NAMES"
fi

if [ -z ${DEPLOY_ENVIRONMENT_NAMES+x} ]; then
    DEPLOY_ENVIRONMENT_NAMES=("${BRANCH}")
else
    IFS=',' read -r -a DEPLOY_ENVIRONMENT_NAMES <<< "$DEPLOY_ENVIRONMENT_NAMES"
fi

echo "DEPLOY_ENVIRONMENT_NAMES: '${DEPLOY_ENVIRONMENT_NAMES}'"
echo "DEPLOY_SERVICE_NAMES: '${DEPLOY_SERVICE_NAMES}'"

# Initiate the deploy to each service. This is non-blocking, we'll wait for success/failure
# below.
for DEPLOY_ENVIRONMENT_NAME in "${DEPLOY_ENVIRONMENT_NAMES[@]}"
do
    ECS_CLUSTER="${DEPLOY_ENVIRONMENT_NAME}-ecs-private"
    for DEPLOY_SERVICE_NAME in "${DEPLOY_SERVICE_NAMES[@]}"
    do
        ECS_SERVICE="${DEPLOY_ENVIRONMENT_NAME}-${DEPLOY_SERVICE_NAME}"
        echo "Deploying to the ${ECS_SERVICE} service in ${ECS_CLUSTER} cluster"
        aws ecs update-service --force-new-deployment --cluster ${ECS_CLUSTER} --service ${ECS_SERVICE}
        echo "Deployment to ${ECS_SERVICE} service in ${ECS_CLUSTER} cluster in progress."
    done
done

# Wait for success/failure.
for DEPLOY_ENVIRONMENT_NAME in "${DEPLOY_ENVIRONMENT_NAMES[@]}"
do
    ECS_CLUSTER="${DEPLOY_ENVIRONMENT_NAME}-ecs-private"
    for DEPLOY_SERVICE_NAME in "${DEPLOY_SERVICE_NAMES[@]}"
    do
        ECS_SERVICE="${DEPLOY_ENVIRONMENT_NAME}-${DEPLOY_SERVICE_NAME}"
        echo "Waiting on the ${ECS_SERVICE} service in ${ECS_CLUSTER} cluster to finish deploying... "
        aws ecs wait services-stable --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE}
        echo "Finished waiting on ${ECS_SERVICE} service in ${ECS_CLUSTER} cluster to finish deploying."
    done
done
