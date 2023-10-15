 #!/usr/bin/bash 
cd lambdafunctions/LF2
pip install -r requirements.txt -t package
cd ../../otherscripts/terraform
terraform apply -auto-approve
cd ..
python scrape_yelp.py
python batch_upload2db.py