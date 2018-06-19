PWD = $(shell pwd)

image:
	docker build . -t otabot

lint: image
	docker run --rm otabot pylint **/*.py -E

run: image
	docker run --rm -it otabot

runlocal:
	docker run --rm -it -v ${PWD}/:/src/ otabot
