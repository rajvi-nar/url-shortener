variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  default     = "ca8b2ecd-e3fa-443f-bccf-2553efab18f7"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-url-shortener"
}

variable "cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
  default     = "aks-url-shortener"
}

variable "acr_name" {
  description = "Name of the Azure Container Registry (globally unique, lowercase, no dashes)"
  type        = string
  default     = "urlshortenertest123"
}
