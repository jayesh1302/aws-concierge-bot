provider "aws" {
  region = "us-east-1"
}

locals {
  json_data = file("test.json")
  tf_data   = jsondecode(local.json_data)
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

resource "aws_dynamodb_table_item" "dynamodb_table_item" {
  for_each   = local.tf_data
  table_name = aws_dynamodb_table.dynamodb_table.name
  hash_key   = "id"
  item       = jsonencode(each.value)
}
