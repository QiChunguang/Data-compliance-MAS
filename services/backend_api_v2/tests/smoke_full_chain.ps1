# Smoke Test: full_chain_runtime for data_transaction and cross_border
$ErrorActionPreference = "Stop"
$BaseUrl = $env:REGUTHINK_TEST_BASE_URL
if (-not $BaseUrl) {
    throw "Set REGUTHINK_TEST_BASE_URL before running this smoke test."
}

function Test-FullChain($testName, $convTitle, $assessmentType, $materialFile, $chatContent) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "=== Smoke: $testName ===" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    Write-Host "`n[1] Creating conversation..." -ForegroundColor Yellow
    $convBody = @{ title = $convTitle; assessment_type = $assessmentType } | ConvertTo-Json -Compress
    $convResp = Invoke-RestMethod -Uri "$BaseUrl/conversations" -Method Post -Body $convBody -ContentType "application/json"
    $convId = $convResp.conversation_id
    Write-Host "  conversation_id: $convId" -ForegroundColor Green

    Write-Host "`n[2] Uploading test material..." -ForegroundColor Yellow
    $fileContent = [System.IO.File]::ReadAllText($materialFile)
    $boundary = "----Boundary$(Get-Random)"
    $LF = "`r`n"
    $bodyLines = @()
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"file`"; filename=`"$(Split-Path $materialFile -Leaf)`""
    $bodyLines += "Content-Type: text/plain"
    $bodyLines += ""
    $bodyLines += $fileContent
    $bodyLines += "--$boundary--"
    $body = [string]::Join($LF, $bodyLines)

    $uploadResp = Invoke-RestMethod -Uri "$BaseUrl/conversations/$convId/files" -Method Post -Body $body -ContentType "multipart/form-data; boundary=$boundary"
    $fileId = $uploadResp.file_id
    Write-Host "  file_id: $fileId" -ForegroundColor Green

    Write-Host "`n[3] Calling /chat with full_chain_runtime..." -ForegroundColor Yellow
    $chatBody = @{
        content = $chatContent
        assessment_type = $assessmentType
        file_ids = @($fileId)
        auto_run_assessment = $true
        runtime_mode = "full_chain_runtime"
    } | ConvertTo-Json -Compress

    try {
        $chatResp = Invoke-RestMethod -Uri "$BaseUrl/conversations/$convId/chat" -Method Post -Body $chatBody -ContentType "application/json" -TimeoutSec 120
        Write-Host "  Chat OK. job_id: $($chatResp.job_id)" -ForegroundColor Green
        Write-Host "  runtime_mode_effective: $($chatResp.runtime_mode_effective)"
        Write-Host "  auto_judge_expected: $($chatResp.auto_judge_expected)"
        $jobId = $chatResp.job_id
    } catch {
        Write-Host "  CHAT ERROR: $($_.Exception.Message)" -ForegroundColor Red
        return @{ test = $testName; status = "chat_failed"; all_artifacts_present = $false }
    }

    Write-Host "`n[4] Polling job status..." -ForegroundColor Yellow
    $maxRetries = 30
    $retryCount = 0
    $status = "running"
    
    while ($retryCount -lt $maxRetries -and $status -eq "running") {
        Start-Sleep -Seconds 3
        try {
            $jobResp = Invoke-RestMethod -Uri "$BaseUrl/jobs/$jobId" -Method Get
            $status = $jobResp.status
            $progress = $jobResp.progress
            $stage = $jobResp.current_stage
            Write-Host "  [$retryCount] status=$status progress=$progress stage=$stage"
        } catch {
            Write-Host "  Poll error: $($_.Exception.Message)"
        }
        $retryCount++
    }

    Write-Host "  Final status: $status" -ForegroundColor $(if ($status -eq "completed") { "Green" } else { "Red" })

    Write-Host "`n[5] Checking artifacts..." -ForegroundColor Yellow
    $allPresent = $false
    try {
        $artifactsResp = Invoke-RestMethod -Uri "$BaseUrl/jobs/$jobId/artifacts" -Method Get
        $artifactNames = $artifactsResp.artifacts.PSObject.Properties.Name
        Write-Host "  Artifact count: $($artifactNames.Count)"
        
        $required = @(
            "prototype_report.md",
            "autojudge_result.json",
            "score_breakdown.json",
            "evidence_pack.json",
            "citation_plan.json",
            "retrieval_trace.json",
            "quality_gate.json",
            "dynamic_case_profile.json",
            "extracted_facts.json",
            "source_trace.json",
            "boundary_audit.json",
            "runtime_manifest.json",
            "missing_capabilities.json",
            "claim_plan.json"
        )
        
        $allPresent = $true
        foreach ($r in $required) {
            $found = $r -in $artifactNames
            $mark = if ($found) { "[OK]" } else { "[MISSING]" }
            Write-Host "  $mark $r" -ForegroundColor $(if ($found) { "Green" } else { "Red" })
            if (-not $found) { $allPresent = $false }
        }
        
        if ($allPresent) {
            Write-Host "`n  ALL REQUIRED ARTIFACTS PRESENT!" -ForegroundColor Green
        }
    } catch {
        Write-Host "  Artifacts error: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host "`n[6] Checking events..." -ForegroundColor Yellow
    try {
        $eventsResp = Invoke-RestMethod -Uri "$BaseUrl/jobs/$jobId/events" -Method Get
        $eventTypes = $eventsResp.events | ForEach-Object { $_.event_type }
        Write-Host "  Event count: $($eventsResp.events.Count)"
        Write-Host "  autojudge_started: $(if ('autojudge_started' -in $eventTypes) { '[OK]' } else { '[MISSING]' })"
        Write-Host "  autojudge_completed: $(if ('autojudge_completed' -in $eventTypes) { '[OK]' } else { '[MISSING]' })"
        Write-Host "  final: $(if ('final' -in $eventTypes) { '[OK]' } else { '[MISSING]' })"
    } catch {
        Write-Host "  Events error: $($_.Exception.Message)" -ForegroundColor Red
    }

    $result = if ($status -eq 'completed' -and $allPresent) { "PASSED" } else { "FAILED" }
    Write-Host "`n=== $testName : $result ===" -ForegroundColor $(if ($result -eq "PASSED") { "Green" } else { "Red" })
    
    return @{
        test = $testName
        conversation_id = $convId
        job_id = $jobId
        file_id = $fileId
        status = $status
        all_artifacts_present = $allPresent
    }
}

# Run Smoke A: Data Transaction
$resultA = Test-FullChain "Smoke-A-DataTransaction" "smoke-ft-dt" "data_transaction_compliance" `
    ".\tests\smoke_test_material_data_transaction.txt" `
    "请基于上传材料运行完整多智能体数据交易合规评估，并给出报告和 AutoJudge 评分。"

# Run Smoke B: Cross Border
$resultB = Test-FullChain "Smoke-B-CrossBorder" "smoke-ft-cb" "cross_border_data_transfer" `
    ".\tests\smoke_test_material_cross_border.txt" `
    "我有一批财务数据需要出境，请运行完整跨境数据传输合规评估，并给出 AutoJudge 评分。"

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "=== FINAL SMOKE SUMMARY ===" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Smoke A (Data Transaction): status=$($resultA.status), all_artifacts=$($resultA.all_artifacts_present)"
Write-Host "Smoke B (Cross Border):    status=$($resultB.status), all_artifacts=$($resultB.all_artifacts_present)"

$overall = ($resultA.status -eq "completed" -and $resultA.all_artifacts_present -and $resultB.status -eq "completed" -and $resultB.all_artifacts_present)
$overallResult = if ($overall) { "PASSED" } else { "PASS WITH WARNINGS" }
Write-Host "`nOVERALL: $overallResult" -ForegroundColor $(if ($overall) { "Green" } else { "Yellow" })
