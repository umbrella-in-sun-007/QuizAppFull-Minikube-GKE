#!/bin/bash

OUTPUT_FILE="GCP_INSIGHTS_REPORT.md"

echo "# GCP Insights & Status Report" > $OUTPUT_FILE
echo "Generated on: $(date)" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

echo "## 1. Cloud SQL Status" >> $OUTPUT_FILE
echo "\`\`\`" >> $OUTPUT_FILE
gcloud sql instances describe quizapp-postgres-prod --format="yaml(state,settings.tier,settings.dataDiskSizeGb,ipAddresses)" >> $OUTPUT_FILE
echo "\`\`\`" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

echo "## 2. GKE Cluster Status" >> $OUTPUT_FILE
echo "\`\`\`" >> $OUTPUT_FILE
gcloud container clusters list --format="table(name,location,status,currentNodeCount)" >> $OUTPUT_FILE
echo "\`\`\`" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

echo "## 3. Cloud Storage Buckets" >> $OUTPUT_FILE
echo "\`\`\`" >> $OUTPUT_FILE
gcloud storage buckets list --format="table(name,location,storageClass)" >> $OUTPUT_FILE
echo "\`\`\`" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

echo "## 4. Recent Error Logs (Last 20)" >> $OUTPUT_FILE
echo "\`\`\`" >> $OUTPUT_FILE
gcloud logging read "severity>=ERROR" --limit=20 --format="table(timestamp,severity,textPayload,protoPayload.status.message)" >> $OUTPUT_FILE
echo "\`\`\`" >> $OUTPUT_FILE

echo "Report generated: $OUTPUT_FILE"
