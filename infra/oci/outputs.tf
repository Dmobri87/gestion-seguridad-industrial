output "instance_id" {
  value = oci_core_instance.app.id
}

output "public_ip" {
  value = oci_core_instance.app.public_ip
}

output "ssh_command" {
  value = "ssh ubuntu@${oci_core_instance.app.public_ip}"
}

output "next_steps" {
  value = [
    "1) SSH to VM: ssh ubuntu@${oci_core_instance.app.public_ip}",
    "2) Validate bootstrap logs: sudo cloud-init status --wait",
    "3) Deploy app: cd /opt/gestion_proyectos && bash scripts/oci/deploy.sh",
  ]
}
