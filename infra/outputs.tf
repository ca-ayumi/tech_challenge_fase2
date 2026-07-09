output "ecr_repository_url" {
  description = "URL do repositorio ECR para push da imagem Docker."
  value       = aws_ecr_repository.app.repository_url
}

output "app_url" {
  description = "URL publica do servico App Runner."
  value       = "https://${aws_apprunner_service.app.service_url}"
}

output "app_runner_arn" {
  description = "ARN do servico App Runner."
  value       = aws_apprunner_service.app.arn
}
