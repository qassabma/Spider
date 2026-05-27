# Download Vertex AI batch prediction results for shareddrive_dental_tax_audit_flash_v2
# Run after: gcloud auth login

$GcsPath = "gs://shareddrive_audit_2026/audit_results/prediction-model-2026-05-27T03:22:47.881160Z"
$LocalDir = "$env:USERPROFILE\Downloads\shareddrive_audit_results_2026-05-27"

Write-Host "Listing files in $GcsPath ..."
gcloud storage ls $GcsPath/

Write-Host "`nDownloading to $LocalDir ..."
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null
gcloud storage cp -r "$GcsPath/*" $LocalDir

Write-Host "`nDone. Files saved to:"
Write-Host $LocalDir
Get-ChildItem $LocalDir | Format-Table Name, Length, LastWriteTime
