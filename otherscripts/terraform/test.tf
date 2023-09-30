terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.19.0"
    }
  }
}

provider "aws" {
}

resource "aws_dynamodb_table" "dynamodb_table" {
  name         = "yelp-restaurants"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }
}

resource "aws_opensearch_domain" "opensearch" {
  domain_name    = "restaurants"
  engine_version = "Elasticsearch_7.10"

  cluster_config {
    instance_type = "t3.small.search"
  }
  ebs_options {
    ebs_enabled = true
    volume_size = 10
  }
}
