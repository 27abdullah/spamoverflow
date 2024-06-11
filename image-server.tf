resource "docker_image" "spamoverflow" {
  name = "${aws_ecr_repository.spamoverflow.repository_url}:server"
  build {
    context = "."
    dockerfile = "Dockerfile-server"
  }
}
resource "docker_registry_image" "spamoverflow" {
  name = docker_image.spamoverflow.name
}