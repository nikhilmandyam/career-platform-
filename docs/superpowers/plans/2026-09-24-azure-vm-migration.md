# Azure VM Migration Plan

This plan records the intended migration of the career platform to an Azure Ubuntu VM and the work completed for Exercise 03. Azure subscription policy blocked VM creation, so the migration did not reach the VM setup stages.

## Server

- **Where:** Azure CLI commands ran on my Mac. The intended server was an Ubuntu VM in Azure.
- **Planned:** Create resource group `rg-career-platform` and VM `vm-career-platform` with size `Standard_B2ts_v2` in West US 2, as required by the class guide. Azure CLI was installed, the Azure for Students subscription was activated, login/authentication succeeded, and an SSH key pair was created at `~/.ssh/isba4775_azure`. The public key was prepared for Azure. When West US 2 failed, I used Azure CLI to investigate regions offering `Standard_B2ts_v2` and also attempted West Central US and Chile Central.
- **Why:** Host the resume application on the VM required by the exercise, using a region and size specified by the class guide.
- **How it would be checked:** Confirm the VM is provisioned with the requested name, Ubuntu image, size, and region in Azure.
- **Rollback/undo:** If a VM were created, deallocate and delete it, then remove the resource group if it contains no resources that need to be kept.
- **Actual result:** Azure CLI installation, subscription activation, and login succeeded. VM creation in West US 2 failed with `RequestDisallowedByAzure` because of Azure subscription regional policy. West Central US and Chile Central were also attempted and failed with the same regional-policy error. No VM was successfully created.

## Packages

- **Where:** On the intended Ubuntu VM, after connecting over SSH.
- **Planned:** Install the system packages needed for Python, application deployment, and MySQL connectivity.
- **Why:** The VM needs the runtime and supporting system tools to host the application.
- **How it would be checked:** Check installed package versions and confirm the required executables are available.
- **Rollback/undo:** Remove packages installed for the application if they are no longer needed.
- **Actual result:** NOT REACHED. No VM existed and SSH access was not possible.

## Code

- **Where:** On the intended Ubuntu VM, in the application directory.
- **Planned:** Transfer or clone the reviewed application code from the repository.
- **Why:** Make the resume application available on the server.
- **How it would be checked:** Confirm the expected application files and Git revision are present on the VM.
- **Rollback/undo:** Restore the previous application revision or remove the deployed application directory.
- **Actual result:** NOT REACHED. No VM existed, so code was not transferred.

## Python

- **Where:** On the intended Ubuntu VM, in the application directory.
- **Planned:** Create a Python virtual environment and install the dependencies listed by the application.
- **Why:** Isolate the application's Python packages from the system Python installation.
- **How it would be checked:** Confirm the virtual environment is active, dependencies install successfully, and the application imports.
- **Rollback/undo:** Stop using and remove the application virtual environment; recreate it from the dependency list if needed.
- **Actual result:** NOT REACHED. Python environment setup could not begin without a VM.

## Config

- **Where:** On the intended Ubuntu VM, using deployment-specific environment configuration.
- **Planned:** Configure the application for the server, including its database connection and listening settings, without placing secrets in source control.
- **Why:** The deployed application needs server-specific settings to connect to its database and serve requests.
- **How it would be checked:** Review the configuration on the VM and confirm the application can load it without exposing secrets.
- **Rollback/undo:** Restore a saved configuration or remove deployment-specific settings and return to the prior known-good configuration.
- **Actual result:** NOT REACHED. No server configuration was created.

## Data

- **Where:** On the intended Ubuntu VM or its local database service.
- **Planned:** Set up the database and transfer or initialize the project data required by the application.
- **Why:** The resume site's project list is database-backed.
- **How it would be checked:** Confirm the database is reachable and the expected project records can be read by the application.
- **Rollback/undo:** Preserve a database backup, then restore it or remove only the deployment data if rollback is required.
- **Actual result:** NOT REACHED. Data transfer and database setup on Azure were not performed.

## Processes

- **Where:** On the intended Ubuntu VM.
- **Planned:** Start the application as a managed process so it remains available after the SSH session ends.
- **Why:** The site must continue serving visitors reliably.
- **How it would be checked:** Inspect the process or service status and request the application locally on the VM.
- **Rollback/undo:** Stop and disable the application service, then restore its previous service configuration if one existed.
- **Actual result:** NOT REACHED. The application was not started on a VM.

## Verify

- **Where:** Azure CLI and portal for resource checks; SSH and HTTP requests from an external client for server and site checks.
- **Planned:** Verify VM provisioning, SSH access, application startup, external access to port 8000, and the requested site screenshot.
- **Why:** These checks demonstrate that the migration produced a working, reachable site.
- **How it would be checked:** Confirm Azure resource details, connect over SSH, check the application process, request the site over HTTP on port 8000, and capture the site screenshot.
- **Rollback/undo:** If verification fails, stop the application and deallocate the VM while diagnosing; delete deployment resources if abandoning the migration.
- **Actual result:** VM-dependent checks were not possible because Azure policy prevented VM creation. Individual outcomes are listed in the Verify results table at the end of this plan.

## Shutdown

- **Where:** Azure CLI or Azure portal, after completing server verification.
- **Planned:** Deallocate the VM when it is not in use, or delete the VM and resource group when the exercise is complete and resources are no longer needed.
- **Why:** Avoid leaving unneeded compute resources running and reduce ongoing Azure costs.
- **How it would be checked:** Confirm the VM reports a deallocated or deleted state in Azure.
- **Rollback/undo:** Start a deallocated VM again if it is still needed; restore from backups or redeploy if it was deleted.
- **Actual result:** NOT REACHED. No VM was created, so there was nothing to deallocate or shut down.

## Verify results

| Check | Status | Evidence |
|---|---|---|
| Azure CLI installed | PASS | Azure CLI installed successfully on my Mac. |
| Azure subscription active | PASS | Azure for Students subscription activated successfully. |
| Azure login successful | PASS | Azure CLI login/authentication succeeded. |
| SSH key created | PASS | Key pair created at `~/.ssh/isba4775_azure`; public key prepared for Azure. |
| VM deployment in West US 2 | FAIL | `RequestDisallowedByAzure` due to subscription regional policy. |
| VM deployment in West Central US | FAIL | Same `RequestDisallowedByAzure` regional-policy error. |
| VM deployment in Chile Central | FAIL | Same `RequestDisallowedByAzure` regional-policy error. |
| VM created | FAIL | Azure blocked resource creation; no VM was successfully created. |
| Public IP assigned | NOT REACHED | No VM existed to receive a public IP. |
| SSH connection | NOT REACHED | No VM existed to connect to. |
| App running on VM | NOT REACHED | No VM existed; application startup was not reached. |
| Port 8000 external verification | NOT REACHED | No VM or public IP existed for an external request. |
| Site screenshot | NOT REACHED | No public server existed to capture. |
| VM deallocated | NOT REACHED | No VM was created to deallocate. |
