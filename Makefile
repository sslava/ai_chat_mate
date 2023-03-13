SHELL:= /bin/bash
SERVICE_ACCOUNT:=${SERVICE_ACCOUNT}

configure:
	@echo '${SERVICE_ACCOUNT}' > keyfile.txt
	gcloud auth activate-service-account --key-file keyfile.txt; rm keyfile.txt || true

build:
	gcloud --project ${PROJECT_ID} builds submit . --region ${REGION} --suppress-logs --tag ${IMAGE} || true

deploy:
	gcloud --project ${PROJECT_ID} run deploy telegram-bot --region ${REGION} --image ${IMAGE} --max-instances=1 --memory=256Mi --cpu=1 --port=8080

cd_build: configure build

cd_deploy: configure deploy