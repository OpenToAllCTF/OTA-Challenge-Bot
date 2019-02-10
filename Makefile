PWD = $(shell pwd)

build:
	docker build . -t otabot

image:
	docker images | grep otabot || docker build . -t otabot

lint: image
	docker run --rm -v ${PWD}/:/src/ otabot pylint **/*.py -E

run: build
	docker run --rm -it otabot

runlocal: image
	docker run --rm -it -v ${PWD}/:/src/ otabot

background: image
	docker run --rm -d --name otabot otabot

stop:
	docker stop otabot
