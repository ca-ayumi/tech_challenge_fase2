variable "regiao" {
  description = "Regiao AWS onde os recursos serao criados."
  type        = string
  default     = "us-east-1"
}

variable "nome_projeto" {
  description = "Prefixo de nomeacao dos recursos."
  type        = string
  default     = "rota-medica"
}

variable "llm_provider" {
  description = "Provedor de LLM: 'gemini', 'openai' ou vazio (autodeteccao)."
  type        = string
  default     = "gemini"
}

variable "gemini_api_key" {
  description = "Chave do Google Gemini (camada gratuita)."
  type        = string
  sensitive   = true
  default     = ""
}

variable "gemini_model" {
  description = "Modelo do Gemini a ser utilizado."
  type        = string
  default     = "gemini-2.0-flash"
}

variable "openai_api_key" {
  description = "Chave da API da OpenAI injetada como variavel de ambiente no servico."
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_model" {
  description = "Modelo de chat da OpenAI a ser utilizado."
  type        = string
  default     = "gpt-4o-mini"
}

variable "cpu" {
  description = "vCPU do servico App Runner (ex.: 1024 = 1 vCPU)."
  type        = string
  default     = "1024"
}

variable "memoria" {
  description = "Memoria do servico App Runner em MB."
  type        = string
  default     = "2048"
}

variable "tag_imagem" {
  description = "Tag da imagem Docker publicada no ECR."
  type        = string
  default     = "latest"
}
