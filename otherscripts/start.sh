 #!/usr/bin/bash 
cd terraform
terraform apply -auto-approve
cd ..
python scrape_yelp.py
python batch_upload2db.py