variable "tenancy_ocid" {
  type        = string
  description = "OCI Tenancy OCID"
}

variable "user_ocid" {
  type        = string
  description = "OCI User OCID"
}

variable "fingerprint" {
  type        = string
  description = "API key fingerprint"
}

variable "private_key_path" {
  type        = string
  description = "Path to OCI API private key"
}

variable "region" {
  type        = string
  description = "OCI region, e.g. us-ashburn-1"
}

variable "compartment_ocid" {
  type        = string
  description = "Target compartment OCID"
}

variable "availability_domain" {
  type        = string
  description = "Availability domain name, e.g. Uocm:US-ASHBURN-AD-1"
}

variable "ssh_public_key_path" {
  type        = string
  description = "Path to public SSH key for instance access"
}

variable "instance_shape" {
  type        = string
  description = "Compute shape"
  default     = "VM.Standard.A1.Flex"
}

variable "ocpus" {
  type        = number
  description = "Number of OCPUs for flex shape"
  default     = 2
}

variable "memory_in_gbs" {
  type        = number
  description = "Memory in GB for flex shape"
  default     = 12
}

variable "boot_volume_size_in_gbs" {
  type        = number
  description = "Boot volume size"
  default     = 80
}

variable "instance_display_name" {
  type        = string
  description = "Compute instance name"
  default     = "gestion-proyectos-prod"
}

variable "vcn_cidr_block" {
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr_block" {
  type        = string
  default     = "10.0.1.0/24"
}

variable "source_image_ocid" {
  type        = string
  description = "Boot image OCID (Ubuntu ARM image OCID in your region)"
}

variable "extra_block_volume_size_gbs" {
  type        = number
  description = "Extra block volume size"
  default     = 50
}

variable "create_extra_block_volume" {
  type        = bool
  default     = true
}

variable "repo_url" {
  type        = string
  description = "Git repository URL to clone on VM"
}

variable "repo_branch" {
  type        = string
  default     = "main"
}

variable "allowed_ssh_cidr" {
  type        = string
  description = "CIDR allowed to SSH (set your public IP/32)"
  default     = "0.0.0.0/0"
}
