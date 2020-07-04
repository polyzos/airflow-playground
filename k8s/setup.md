Setup airflow on k8s Cluster using Helm
------------------------------
1. helm repo add stable https://kubernetes-charts.storage.googleapis.com/
2. helm search repo stable
3. helm repo update
4. helm search repo airflow 
5. helm show values stable/airflow >> values.yaml
6. helm install -f values.yaml airflow  stable/airflow
7. change image repository to use mine, that has the dags folder
8. export POD_NAME=$(kubectl get pods --namespace default -l "component=web,app=airflow" -o jsonpath="{.items[0].metadata.name}")
9. kubectl port-forward --namespace default $POD_NAME 8080:8080
10. helm uninstall airflow   

Add Dags
1. docker build -t polyzos/airflow . 
2. docker push polyzos/airflow 