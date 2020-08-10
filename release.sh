#!/usr/bin/env bash

set -e

PROJECT_NAME="cuphd-health-status-service"
GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if [[ "${GIT_BRANCH}" = "master" ]]; then
    VERSION=${VERSION:-"$(git describe --abbrev=0 --tags)"}
elif [[ "${GIT_BRANCH}" = "deploy" ]]; then
    VERSION="stage"
else
    exit 0
fi

aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 430229884637.dkr.ecr.us-east-2.amazonaws.com

docker build -f Dockerfile -t ${PROJECT_NAME}:${VERSION} .
docker tag ${PROJECT_NAME}:${VERSION} 430229884637.dkr.ecr.us-east-2.amazonaws.com/${PROJECT_NAME}:${VERSION}
docker push 430229884637.dkr.ecr.us-east-2.amazonaws.com/${PROJECT_NAME}:${VERSION}
