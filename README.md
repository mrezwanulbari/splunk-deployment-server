# Enterprise Splunk Deployment Automation
This project automates the deployment and configuration of Splunk across multiple nodes in a large-scale enterprise environment. By leveraging industry best practices and Splunk's deployment features, it streamlines the installation, configuration, and management of Splunk deployments.
  
## Features
- Full Splunk deployment automation using Ansible
- Centralized configuration management
- Secure access management using predefined roles

## Benefits
- Reduces manual errors and deployment time by up to 70%
- Enables rapid scaling and remote management

![Splunk](https://img.shields.io/badge/Splunk-000000?style=for-the-badge&logo=splunk&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Contributions](https://img.shields.io/badge/Contributions-Welcome-brightgreen.svg)

> A comprehensive repository for designing, deploying, and managing Splunk Deployment Servers at enterprise scale. Covers server class architecture, app deployment strategies, forwarder management, and production-hardened configurations.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [Configuration Reference](#configuration-reference)
- [Deployment Workflow](#deployment-workflow)
- [Scaling & High Availability](#scaling--high-availability)
- [Monitoring & Health Checks](#monitoring--health-checks)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The **Splunk Deployment Server (DS)** is a centralized configuration management tool that distributes apps, configurations, and content to Splunk Universal Forwarders (UFs) and other Splunk instances across an enterprise environment.

### Why This Repository?

- **Standardized Deployment Patterns**: Proven architectures for managing 1,000–100,000+ forwarders
- **Production-Ready Configs**: Battle-tested `serverclass.conf`, `deploymentclient.conf`, and supporting configurations
- **Automation Scripts**: Health checks, bulk deployment, and client management tooling
- **Scalability Guidance**: Multi-tier DS design for large-scale SIEM operations

### Key Capabilities

| Capability | Description |
|---|---|
| Centralized App Management | Push apps and configs to thousands of forwarders |
| Server Class Architecture | Group clients by role, OS, location, or data source |
| Phased Rollout | Canary and staged deployment strategies |
| Forwarder Lifecycle | Onboard, update, and decommission forwarders |
| Compliance Enforcement | Ensure consistent logging standards across infrastructure |

---

## Architecture

### Single-Tier Architecture (up to 5,000 clients)

```
┌─────────────────────────────────────────────────┐
│                Deployment Server                 │
│            (serverclass.conf)                    │
│         ┌─────────┬─────────┬─────────┐         │
│         │ App A   │ App B   │ App C   │         │
│         └────┬────┴────┬────┴────┬────┘         │
└──────────────┼─────────┼─────────┼──────────────┘
               │         │         │
    ┌──────────▼──┐  ┌───▼──────┐  ┌▼───────────┐
    │ Windows UFs │  │ Linux UFs│  │ Network UFs │
    │ (ServerClass│  │(ServerCl.│  │ (ServerCl.  │
    │  windows)   │  │  linux)  │  │  network)   │
    └─────────────┘  └──────────┘  └─────────────┘
```

### Multi-Tier Architecture (10,000+ clients)

```
┌──────────────────────┐
│   Primary DS (Mgmt)  │
│  serverclass.conf    │
└──────────┬───────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐  ┌────▼───┐
│ DS-East│  │DS-West │   (Regional Deployment Servers)
│        │  │        │
└───┬────┘  └────┬───┘
    │             │
┌───▼─────────────▼───┐
│   Universal          │
│   Forwarders         │
│   (Region-Specific)  │
└──────────────────────┘
```

---

## Repository Structure

```
splunk-deployment-server/
├── README.md
├── configs/
│   ├── serverclass.conf              # Server class definitions
│   ├── deploymentclient.conf         # Forwarder-side DS client config
│   ├── server.conf                   # DS server settings
│   └── outputs.conf                  # Forwarding configuration
├── deployment-apps/
│   ├── org_all_forwarder_outputs/    # Base output config for all UFs
│   │   └── local/outputs.conf
│   ├── org_full_license_server/      # License server pointer
│   │   └── local/server.conf
│   ├── org_indexer_discovery/        # Indexer discovery configuration
│   │   └── local/outputs.conf
│   ├── org_cluster_forwarder_outputs/
│   │   └── local/outputs.conf
│   └── org_all_deploymentclient/     # DS client phone-home config
│       └── local/deploymentclient.conf
├── scripts/
│   ├── health_check.sh               # DS health monitoring script
│   ├── deploy_apps.sh                # Bulk app deployment script
│   ├── client_status.py              # Forwarder status report
│   └── cleanup_stale_clients.py      # Remove inactive clients
├── docs/
│   ├── architecture-guide.md         # Detailed architecture reference
│   ├── deployment-workflow.md        # Step-by-step deployment process
│   ├── scaling-guide.md              # Scaling to 100K+ forwarders
│   └── troubleshooting.md           # Common issues and solutions
└── monitoring/
    ├── ds_health_dashboard.xml       # Splunk dashboard for DS monitoring
    └── ds_alerts.conf                # Alert definitions for DS issues
```

---

## Quick Start

### Prerequisites

- Splunk Enterprise 9.x+ installed
- Network connectivity on port **8089** (management) between DS and clients
- Sufficient disk space for deployment apps (varies by environment)

### Step 1: Configure the Deployment Server

```bash
# Copy server.conf to your Splunk instance
cp configs/server.conf $SPLUNK_HOME/etc/system/local/server.conf
```

### Step 2: Define Server Classes

```bash
# Copy serverclass.conf
cp configs/serverclass.conf $SPLUNK_HOME/etc/system/local/serverclass.conf

# Reload the deployment server
$SPLUNK_HOME/bin/splunk reload deploy-server
```

### Step 3: Configure Forwarder Clients

```bash
# On each forwarder, configure the deployment client
cp configs/deploymentclient.conf $SPLUNK_HOME/etc/system/local/deploymentclient.conf

# Restart the forwarder
$SPLUNK_HOME/bin/splunk restart
```

---

## Configuration Reference

### serverclass.conf — Core Concepts

| Stanza | Purpose | Example |
|---|---|---|
| `[global]` | Default settings for all server classes | `repositoryLocation = $SPLUNK_HOME/etc/deployment-apps` |
| `[serverClass:name]` | Define a logical group of clients | `[serverClass:Windows_Servers]` |
| `[serverClass:name:app:appname]` | Map an app to a server class | `[serverClass:Windows_Servers:app:org_win_inputs]` |

### Filtering Clients

```ini
# Match by hostname pattern
whitelist.0 = web-server-*
whitelist.1 = db-server-*

# Match by IP/CIDR
whitelist.2 = 10.10.0.0/16

# Match by machine type
machineTypesFilter = linux-x86_64

# Exclude specific hosts
blacklist.0 = test-*
```

---

## Scaling & High Availability

| Scale | Architecture | Recommendations |
|---|---|---|
| < 1,000 UFs | Single DS | Default config, 30s phone-home |
| 1,000–5,000 UFs | Single DS (tuned) | Increase phone-home to 300s, optimize I/O |
| 5,000–50,000 UFs | Multi-DS with LB | Regional DS instances behind load balancer |
| 50,000+ UFs | Tiered DS hierarchy | Primary + regional DS, staggered phone-home |

### Performance Tuning

```ini
# server.conf - Tuning for large environments
[deployment]
# Increase max clients
maxClients = 50000
# Reduce DS processing threads
streamInWriteTimeout = 10
```

---

## Monitoring & Health Checks

Use the included monitoring dashboard and health check scripts:

```bash
# Run health check
bash scripts/health_check.sh

# Generate client status report
python3 scripts/client_status.py --output report.csv
```

---

## Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| Clients not checking in | Firewall blocking 8089 | Verify network connectivity |
| Apps not deploying | serverclass.conf syntax error | Run `btool check` |
| High DS CPU usage | Too many clients, short phone-home interval | Increase `phoneHomeIntervalInSecs` |
| Stale client entries | Decommissioned forwarders | Run `cleanup_stale_clients.py` |

---

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for any improvements.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

> **Maintained by [Shakil Md. Rezwanul Bari](https://github.com/mrezwanulbari)** — Cybersecurity & SIEM Engineer focused on enterprise security operations and critical infrastructure protection.
