#!/bin/bash

echo "🧪 Deploying test pods to Kubernetes..."
echo ""

# Create test deployment YAMLs
cat > /tmp/k8s-test-nginx-healthy.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-healthy
  labels:
    app: nginx-healthy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx-healthy
  template:
    metadata:
      labels:
        app: nginx-healthy
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
EOF

cat > /tmp/k8s-test-crashloop.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crashloop-app
  labels:
    app: crashloop
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crashloop
  template:
    metadata:
      labels:
        app: crashloop
    spec:
      containers:
      - name: failing-app
        image: busybox
        command: ["/bin/sh", "-c"]
        args:
          - |
            echo "Attempting to connect to database..."
            echo "Error: Failed to connect to database at db.example.com:5432"
            echo "Connection refused"
            exit 1
EOF

cat > /tmp/k8s-test-imagepull.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: imagepull-fail
  labels:
    app: imagepull
spec:
  replicas: 1
  selector:
    matchLabels:
      app: imagepull
  template:
    metadata:
      labels:
        app: imagepull
    spec:
      containers:
      - name: nonexistent
        image: nonexistent-registry.io/fake-app:v1.0.0
EOF

echo "1️⃣  Deploying healthy nginx..."
kubectl apply -f /tmp/k8s-test-nginx-healthy.yaml

echo ""
echo "2️⃣  Deploying crashloop app..."
kubectl apply -f /tmp/k8s-test-crashloop.yaml

echo ""
echo "3️⃣  Deploying imagepull fail app..."
kubectl apply -f /tmp/k8s-test-imagepull.yaml

echo ""
echo "⏳ Waiting 30 seconds for pods to reach their states..."
sleep 30

echo ""
echo "📊 Current pod status:"
kubectl get pods

echo ""
echo "✅ Test deployments created!"
echo ""
echo "💡 Now try these in the chat UI:"
echo "   - What's wrong in my cluster?"
echo "   - Why is crashloop-app crashing?"
echo "   - List all pods"
echo ""
echo "🧹 To clean up: kubectl delete deployment nginx-healthy crashloop-app imagepull-fail"
