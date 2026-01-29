# ☸️ Kubernetes Local Dev Environment (Minikube)

This guide details how to spin up the full application stack (React Frontend + Spring Boot Backend + Postgres) locally using **Minikube**.

## 🛠 Prerequisites

Ensure you have the following installed on your Linux/Proxmox host:

### 1. Install Kubectl (The CLI)

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

```

### 2. Install Minikube (The Cluster)

```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

```

---

## 🚀 Cluster Management

| Action | Command | Description |
| --- | --- | --- |
| **Start** | `minikube start` | Boots up the cluster. |
| **Stop** | `minikube stop` | Pauses the cluster (preserves data). |
| **Delete** | `minikube delete` | Wipes the cluster & data (Factory Reset). |
| **Status** | `minikube status` | Checks if the cluster is running. |
| **Dashboard** | `minikube dashboard` | Opens the web UI (run on desktop). |

---

## 📦 Deployment Workflow

### Step 1: Prepare Images

You have two options to get your code into the cluster.

**Option A: The "Docker Hub" Way (Recommended)**
If your Jenkins pipeline successfully pushed images to Docker Hub:

* Ensure your `k8s-dev.yaml` uses your username: `image: YOUR_USER/my-backend:latest`.
* Kubernetes will download them automatically.

**Option B: The "Manual Load" Way (Local Only)**
If you built images locally on the host and want Minikube to use them without internet:

```bash
minikube image load my-backend:latest
minikube image load my-frontend:latest

```

* *Note:* Your YAML must have `imagePullPolicy: Never` for this to work.

### Step 2: Deploy the Stack

Run this command whenever you change the `k8s-dev.yaml` file:

```bash
kubectl apply -f k8s-dev.yaml

```

### Step 3: Verify Status

Watch the pods come alive:

```bash
kubectl get pods -w

```

* **Success:** Status is `Running` (1/1).
* **Wait:** `ContainerCreating` means it is downloading/starting.
* **Fail:** `CrashLoopBackOff` or `ErrImagePull` (See Troubleshooting).

---

## 🌐 Accessing the Application

Since Minikube runs inside a virtual environment on your server, you cannot access it directly via `localhost`.

### Method 1: Port Forwarding (Best for Proxmox/Remote)

Run this command to forward the cluster's internal port to your server's public IP.

**For the Frontend (React):**

```bash
# Listen on all interfaces (0.0.0.0) so you can access it from your laptop
kubectl port-forward svc/frontend-service 30000:80 --address 0.0.0.0

```

* **URL:** `http://<YOUR_PROXMOX_IP>:30000`

**For the Backend (API):**

```bash
kubectl port-forward svc/backend-service 8080:8080 --address 0.0.0.0

```

### Method 2: Minikube Service URL (Desktop Only)

If you are running Linux with a GUI (Desktop):

```bash
minikube service frontend-service

```

---

## 🐛 Troubleshooting

**1. `ErrImagePull` / `ImagePullBackOff**`

* **Cause:** K8s tried to download the image but failed.
* **Fix:**
* Check spelling of the image name.
* If using **Option B**, ensure `imagePullPolicy: Never` is set in YAML.
* If using **Option A**, ensure the repo is public on Docker Hub.



**2. `CrashLoopBackOff` (Backend)**

* **Cause:** App started, but crashed immediately. Usually "Connection Refused" to DB.
* **Fix:** Check logs to see the error.
```bash
kubectl logs deployment/backend

```


* *Solution:* Ensure the `initContainer` (wait-for-db) is configured in your YAML.



**3. "Service Refused" on Browser**

* **Cause:** The Port Forward command stopped running.
* **Fix:** The `kubectl port-forward` command must stay running in the terminal. If you close the terminal, the connection closes. Use `tmux` or `nohup` to keep it running in the background.