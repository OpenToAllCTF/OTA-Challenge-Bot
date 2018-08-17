PWD = $(shell pwd)

image:
	docker build . -t otabot

lint:
	docker run --rm -v ${PWD}/:/src/ otabot pylint **/*.py -E

run: image
	docker run --rm -it otabot

runlocal:
	docker run --rm -it -v ${PWD}/:/src/ otabot
