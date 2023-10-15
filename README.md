# aws-concierge-bot
Assignment 1 for Cloud-Computing-AWS-CSGY-9223

# How to use
1. Install [remote container](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension on your VS code. Open this repository folder in VS Code and start the dev environment in container.

2. Configure your AWS credentials
```bash
aws configure
# AWS Access Key ID []: <your_key>
# AWS Secret Access Key []: <your_value>
# Default region name [None]: us-east-1
# Default output format [json]: json
```

3. Copy `dot-env-example` env config file and rename to `.env`. Configure the env var accordingly

4. Scrape the restaurant data from yelp and provision DynamoDB and OpenSearch instances on AWS and dump the data to the cloud.
```bash
cd otherscripts
chmod +x start.sh
./start.sh
```

## Terraform
```bash
# Install terraform packages
terraform init
# see the changes
terraform plan
# reduce the scope
terraform plan -target="<resource>.<resource_name>"
# apply the changes
terraform apply
# delete the changes
terraform destroy
```
# Chatbot Recording
Chatbot_Recording.wmv is available which shows the first MVP screen recording. More features may have been added by the time the assignment is submitted. 
Features from the problem statement are covered by the first MVP. 
