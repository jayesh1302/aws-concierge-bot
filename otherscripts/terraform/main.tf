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

/*-----------------SQS-----------------*/
resource "aws_sqs_queue" "Q1_test" {
  name = "Q1-test"
}
data "aws_iam_policy_document" "Q1_test_iam_policy" {
  statement {
    sid    = "First"
    effect = "Allow"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.Q1_test.arn]
  }
}
resource "aws_sqs_queue_policy" "test" {
  queue_url = aws_sqs_queue.Q1_test.id
  policy    = data.aws_iam_policy_document.Q1_test_iam_policy.json
}

/*-----------------LB2-----------------*/
variable "sender_email" {}
variable "es_host" {}
data "archive_file" "python_lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/lf2/package"
  output_path = "lf2.zip"
}
resource "aws_iam_role" "lambda_exec" {
  name = "lf2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Sid    = ""
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      }
    ]
  })
}
resource "aws_iam_role_policy_attachment" "lambda_policy" {
  for_each = toset([
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/AmazonSQSFullAccess",
    "arn:aws:iam::aws:policy/AmazonOpenSearchServiceReadOnlyAccess",
    "arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess",
    "arn:aws:iam::aws:policy/AmazonSESFullAccess"
  ])

  role       = aws_iam_role.lambda_exec.name
  policy_arn = each.value
}
resource "aws_lambda_function" "lf2" {
  function_name = "LF2"
  filename      = "lf2.zip"
  runtime       = "python3.11"
  handler       = "lf2.lambda_handler"
  role          = aws_iam_role.lambda_exec.arn
  timeout       = 15
  environment {
    variables = {
      TF_VAR_es_host      = var.es_host,
      TF_VAR_sender_email = var.sender_email
    }
  }
}

/*-----------------CloudWatch trigger-----------------*/
resource "aws_cloudwatch_event_rule" "lf2_trigger" {
  name                = "lf2-trigger"
  description         = "Schedule lf2 function"
  schedule_expression = "rate(60 minutes)"
}
resource "aws_cloudwatch_event_target" "lf2_target" {
  target_id = "lf2-target"
  rule      = aws_cloudwatch_event_rule.lf2_trigger.name
  arn       = aws_lambda_function.lf2.arn
}
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lf2.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lf2_trigger.arn
}

/*-----------------SES-----------------*/
resource "aws_ses_email_identity" "example" {
  email = var.sender_email
}

/*-----------------DYNAMODB-----------------*/
resource "aws_dynamodb_table" "dynamodb_table" {
  name         = "yelp-restaurants"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }
}

/*-----------------OPENSEARCH-----------------*/
data "aws_caller_identity" "current" {}

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
  access_policies = <<POLICY
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "es:*",
        "Principal": {
          "AWS": ${aws_iam_role.lambda_exec.arn}
        },
        "Effect": "Allow",
        "Resource": "arn:aws:es:us-east-1:${data.aws_caller_identity.current.account_id}:domain/restaurants/*",
      }
    ]
  }
  POLICY
}
