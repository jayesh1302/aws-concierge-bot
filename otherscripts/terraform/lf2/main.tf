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

data "archive_file" "python_lambda_package" {
  type        = "zip"
  source_file = "${path.module}/../../lf2.py"
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
    "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole",

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
}

# CloudWatch trigger
resource "aws_cloudwatch_event_rule" "lf2_trigger" {
  name                = "lf2-trigger"
  description         = "Schedule lf2 function"
  schedule_expression = "rate(1 minute)"
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

