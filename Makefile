build:
	@echo
	@echo --- rebuilding image ---
	docker build -t certitude:dev .

test-train:
	@echo
	@echo --- creating new model using labelled dataset ---
	docker run -it -v $$(pwd)/tests/data:/data certitude:dev --train /data/newmodel101.joblib -d /data/testset_labeled.csv

test-use-existing-model-unlabelled-batch:
	@echo
	@echo --- classifying batch of url against existing model ---
	docker run -it -v $$(pwd)/tests/data:/data certitude:dev -m /data/newmodel101.joblib --batch /data/testset.csv

test-single:
	@echo
	@echo --- classifying single url against existing model ---
	docker run -it -v $$(pwd)/tests/data:/data certitude:dev --url https://www.google.com -m /data/newmodel101.joblib

delete:
	@echo
	@echo --- deleting existing model ---
	rm $$(pwd)/tests/data/newmodel101.joblib || true

demo: delete build test-train test-use-existing-model-unlabelled-batch test-single delete
	@echo
	@echo --- Everything OK ---
