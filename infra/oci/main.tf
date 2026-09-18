locals {
  ssh_public_key = trimspace(file(var.ssh_public_key_path))

  cloud_init = <<-EOT
    #cloud-config
    package_update: true
    package_upgrade: true
    packages:
      - git
      - curl
      - ca-certificates

    runcmd:
      - [ bash, -lc, "git clone ${var.repo_url} /opt/gestion_proyectos || true" ]
      - [ bash, -lc, "cd /opt/gestion_proyectos && git fetch --all && git checkout ${var.repo_branch} && git pull --ff-only origin ${var.repo_branch}" ]
      - [ bash, -lc, "cd /opt/gestion_proyectos && chmod +x scripts/oci/bootstrap-vm.sh scripts/oci/deploy.sh scripts/oci/update.sh || true" ]
      - [ bash, -lc, "cd /opt/gestion_proyectos && bash scripts/oci/bootstrap-vm.sh" ]
  EOT
}

resource "oci_core_vcn" "main" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = [var.vcn_cidr_block]
  display_name   = "gestion-vcn"
  dns_label      = "gestionvcn"
}

resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "gestion-igw"
  enabled        = true
}

resource "oci_core_route_table" "public_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "gestion-public-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.igw.id
  }
}

resource "oci_core_security_list" "public_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "gestion-public-sl"

  ingress_security_rules {
    protocol = "6"
    source   = var.allowed_ssh_cidr
    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 80
      max = 80
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

resource "oci_core_subnet" "public_subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.main.id
  cidr_block                 = var.subnet_cidr_block
  display_name               = "gestion-public-subnet"
  route_table_id             = oci_core_route_table.public_rt.id
  security_list_ids          = [oci_core_security_list.public_sl.id]
  prohibit_public_ip_on_vnic = false
  dns_label                  = "publicsn"
}

resource "oci_core_instance" "app" {
  availability_domain = var.availability_domain
  compartment_id      = var.compartment_ocid
  display_name        = var.instance_display_name
  shape               = var.instance_shape

  shape_config {
    ocpus         = var.ocpus
    memory_in_gbs = var.memory_in_gbs
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.public_subnet.id
    assign_public_ip = true
    display_name     = "gestion-vnic"
    hostname_label   = "gestionhost"
  }

  source_details {
    source_type             = "image"
    source_id               = var.source_image_ocid
    boot_volume_size_in_gbs = var.boot_volume_size_in_gbs
  }

  metadata = {
    ssh_authorized_keys = local.ssh_public_key
    user_data           = base64encode(local.cloud_init)
  }
}

resource "oci_core_volume" "data_volume" {
  count               = var.create_extra_block_volume ? 1 : 0
  compartment_id      = var.compartment_ocid
  availability_domain = var.availability_domain
  display_name        = "gestion-data-volume"
  size_in_gbs         = var.extra_block_volume_size_gbs
}

resource "oci_core_volume_attachment" "data_attach" {
  count           = var.create_extra_block_volume ? 1 : 0
  attachment_type = "paravirtualized"
  instance_id     = oci_core_instance.app.id
  volume_id       = oci_core_volume.data_volume[0].id
}
