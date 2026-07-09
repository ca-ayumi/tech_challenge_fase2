# Infraestrutura como codigo (IaC) para publicar o app Streamlit na AWS
# usando Amazon ECR (registro da imagem) + AWS App Runner (execucao do container).

locals {
  nome = var.nome_projeto
}

# ----------------------------------------------------------------------------
# Repositorio de imagens (ECR)
# ----------------------------------------------------------------------------
resource "aws_ecr_repository" "app" {
  name                 = local.nome
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ----------------------------------------------------------------------------
# Role que permite ao App Runner puxar a imagem do ECR
# ----------------------------------------------------------------------------
data "aws_iam_policy_document" "apprunner_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["build.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "apprunner_ecr" {
  name               = "${local.nome}-apprunner-ecr"
  assume_role_policy = data.aws_iam_policy_document.apprunner_assume.json
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr" {
  role       = aws_iam_role.apprunner_ecr.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# ----------------------------------------------------------------------------
# Servico App Runner
# ----------------------------------------------------------------------------
resource "aws_apprunner_service" "app" {
  service_name = local.nome

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.app.repository_url}:${var.tag_imagem}"
      image_repository_type = "ECR"

      image_configuration {
        port = "8501"
        runtime_environment_variables = {
          LLM_PROVIDER   = var.llm_provider
          GEMINI_API_KEY = var.gemini_api_key
          GEMINI_MODEL   = var.gemini_model
          OPENAI_API_KEY = var.openai_api_key
          OPENAI_MODEL   = var.openai_model
        }
      }
    }

    auto_deployments_enabled = true
  }

  instance_configuration {
    cpu    = var.cpu
    memory = var.memoria
  }

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/_stcore/health"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }

  tags = {
    Projeto = local.nome
    Origem  = "terraform"
  }
}
