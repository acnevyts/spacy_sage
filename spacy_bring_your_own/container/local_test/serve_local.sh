#!/bin/sh

image=$1
echo Serving
echo "$(pwd)/test_dir:/opt/ml -p 8080:8080 --rm ${image} serve"
docker run -v $(pwd)/test_dir:/opt/ml -p 8080:8080 --rm ${image} serve
echo Done
