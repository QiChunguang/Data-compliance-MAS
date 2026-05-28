# Smoke Test 1: data_transaction_compliance
Write-Host "=== Smoke Test 1: data_transaction_compliance ==="

# Step 1: Create conversation
Write-Host "`n[Step 1] Creating conversation..."
$convBody = @{
    title = "smoke-test-data-transaction"
    assessment_type = "data_transaction_compliance"
} | ConvertTo-Json -Compress

$BaseUrl = $env:REGUTHINK_TEST_BASE_URL
if (-not $BaseUrl) {
    throw "Set REGUTHINK_TEST_BASE_URL before running this smoke test."
}

$convResp = Invoke-RestMethod -Uri "$BaseUrl/conversations" -Method Post -Body $convBody -ContentType "application/json"
$convId = $convResp.conversation_id
Write-Host "  conversation_id: $convId"

# Step 2: Upload file
Write-Host "`n[Step 2] Uploading test material..."
$filePath = ".\tests\smoke_test_material_data_transaction.txt"
$fileBytes = [System.IO.File]::ReadAllBytes($filePath)
$fileContent = [System.IO.File]::ReadAllText($filePath)
$boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
$LF = "`r`n"

$bodyLines = @()
$bodyLines += "--$boundary"
$bodyLines += "Content-Disposition: form-data; name=`"file`"; filename=`"smoke_test_material_data_transaction.txt`""
$bodyLines += "Content-Type: text/plain"
$bodyLines += ""
$bodyLines += $fileContent
$bodyLines += "--$boundary--"
$body = [string]::Join($LF, $bodyLines)

$uploadResp = Invoke-RestMethod -Uri "$BaseUrl/conversations/$convId/files" -Method Post -Body $body -ContentType "multipart/form-data; boundary=$boundary"
$fileId = $uploadResp.file_id
Write-Host "  file_id: $fileId"

# Step 3: Call /chat with uploaded_material_runtime
Write-Host "`n[Step 3] Calling /chat with uploaded_material_runtime..."
$chatBody = @{
    content = "请基于上传材料执行数据交易合规评估，并生成 prototype 合规报告。"
    assessment_type = "data_transaction_compliance"
    file_ids = @($fileId)
    auto_run_assessment = $true
    runtime_mode = "uploaded_material_runtime"
} | ConvertTo-Json -Compress

Write-Host "  Request body: $chatBody"

try {
    $chatResp = Invoke-RestMethod -Uri "$BaseUrl/conversations/$convId/chat" -Method Post -Body $chatBody -ContentType "application/json"
    Write-Host "  Chat response received!"
    Write-Host "  job_id: $($chatResp.job_id)"
    Write-Host "  user_message: $($chatResp.user_message.content.Substring(0, [Math]::Min(100, $chatResp.user_message.content.Length)))..."
    Write-Host "  assistant_message: $($chatResp.assistant_message.content.Substring(0, [Math]::Min(200, $chatResp.assistant_message.content.Length)))..."
    
    $jobId = $chatResp.job_id
    
    # Step 4: Wait and poll job status
    Write-Host "`n[Step 4] Polling job status..."
    Start-Sleep -Seconds 3
    
    $maxRetries = 20
    $retryCount = 0
    $jobDone = $false
    
    while ($retryCount -lt $maxRetries -and -not $jobDone) {
        $jobResp = Invoke-RestMethod -Uri "$BaseUrl/jobs/$jobId" -Method Get
        $status = $jobResp.status
        $progress = $jobResp.progress
        $stage = $jobResp.current_stage
        Write-Host "  [retry $retryCount] status=$status, progress=$progress, stage=$stage"
        
        if ($status -eq "completed" -or $status -eq "failed") {
            $jobDone = $true
            Write-Host "  Job finished with status: $status"
            if ($status -eq "completed") {
                Write-Host "  result_artifacts: $($jobResp.result_artifacts | ConvertTo-Json -Depth 5)"
            } else {
                Write-Host "  error: $($jobResp.error)"
            }
        } else {
            Start-Sleep -Seconds 3
            $retryCount++
        }
    }
    
    # Step 5: Check artifacts
    Write-Host "`n[Step 5] Checking artifacts..."
    try {
        $artifactsResp = Invoke-RestMethod -Uri "$BaseUrl/jobs/$jobId/artifacts" -Method Get
        Write-Host "  Artifacts:"
        $artifactsResp | ConvertTo-Json -Depth 3
    } catch {
        Write-Host "  Artifacts endpoint returned error: $($_.Exception.Message)"
    }
    
    Write-Host "`n=== Smoke Test 1 Summary ==="
    Write-Host "  conversation_id: $convId"
    Write-Host "  file_id: $fileId"
    Write-Host "  job_id: $jobId"
    Write-Host "  final_status: $status"
    
} catch {
    Write-Host "  ERROR: $($_.Exception.Message)"
    try {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "  Response body: $responseBody"
    } catch {}
}
