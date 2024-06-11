resource "aws_sqs_queue" "spamworker_queue" {
  name = "spamworker"
  # content_based_deduplication = true
}