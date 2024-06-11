resource "docker_image" "spamworker" {
  name = "${aws_ecr_repository.spamoverflow.repository_url}:worker"
  build {
    context = "."
    dockerfile = "Dockerfile-worker"
  }
}
resource "docker_registry_image" "spamworker" {
  name = docker_image.spamworker.name
}