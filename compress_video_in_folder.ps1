# 1. 获取用户输入（支持拖入文件或文件夹）
$userInput = Read-Host "请输入或拖入源视频文件，或视频文件夹路径"
$userInput = $userInput.Replace('"', '').Replace("'", "").Replace("“", "").Replace("”", "").Trim()

# 2. 判断输入类型并搜集目标文件
$videoFiles = @()
$isSingleFileMode = $false

if (Test-Path $userInput -PathType Leaf) {
    $fileItem = Get-Item $userInput
    if ($fileItem.Extension -ieq ".mov" -or $fileItem.Extension -ieq ".mp4") {
        $videoFiles += $fileItem
        $isSingleFileMode = $true
    } else {
        Write-Error "输入的单文件格式不是 .mov 或 .mp4！"
        Read-Host "`n按回车键退出..."
        Exit
    }
} elseif (Test-Path $userInput -PathType Container) {
    # 获取文件后，使用 Sort-Object Length 让文件体积从小到大（升序）排队
    $videoFiles = Get-ChildItem -Path $userInput -Include *.mov, *.mp4 -Recurse -File | Sort-Object Length
} else {
    Write-Error "找不到输入的路径，请检查是否存在或拼写正确！"
    Read-Host "`n按回车键退出..."
    Exit
}

if ($videoFiles.Count -eq 0) {
    Write-Warning "未找到任何需要处理的 .mov 或 .mp4 视频文件！"
    Read-Host "`n按回车键退出..."
    Exit
}

# 3. 交互选项配置
Write-Host "`n[NVEnc 质量配置] 18: 媲美 slower (高质量) | 22: 媲美 slow (高性价比甜点默认)" -ForegroundColor Cyan
$qValue = Read-Host "请自定输入 NVEnc Q值 (直接回车默认 22)"
if ([string]::IsNullOrWhiteSpace($qValue)) { $qValue = "22" }

Write-Host "`n[文件处理策略]" -ForegroundColor Cyan
Write-Host "1. 保留原文件 -> 输出为 '文件名_compressed.mp4' (默认)"
Write-Host "2. 覆盖原文件 -> 压制元数据缝合成功后，全自动删除原文件"
$overwriteChoice = Read-Host "请输入选项数字 (默认 1)"
if ([string]::IsNullOrWhiteSpace($overwriteChoice)) { $overwriteChoice = "1" }

if ($isSingleFileMode) {
    Write-Host "`n检测到单文件模式，准备检查并开始压制...`n" -ForegroundColor Green
} else {
    Write-Host "`n检测到文件夹批量模式（已按体积从小到大排序），共找到 $($videoFiles.Count) 个视频，准备开始排队压制...`n" -ForegroundColor Green
}

$successCount = 0
$failCount = 0
$skipCount = 0
$bloatCount = 0

# ✨ 双重元数据识别暗号
$markerTagSuccess = "Compressed_By_NVEnc_P7"
$markerTagBloat   = "Skipped_By_NVEnc_Bloat"

# 4. 队列循环处理
foreach ($file in $videoFiles) {
    $inputPath = $file.FullName
    $parentDir = $file.DirectoryName
    $fileNameOnly = $file.BaseName
    
    # 计算原始大小
    $originalSizeByte = $file.Length
    $originalSizeMB = [Math]::Round($originalSizeByte / 1MB, 2)
    
    Write-Host "--------------------------------------------------" -ForegroundColor Gray
    Write-Host "正在检查 ($($successCount + $failCount + $skipCount + $bloatCount + 1)/$($videoFiles.Count)) [原大小: $originalSizeMB MB]: $($file.Name)" -ForegroundColor Yellow
    
    # 快速检测文件是否包含压缩暗号（无论是成功标还是膨胀标，都触发拦截）
    $checkMarker = & exiftool -s3 -Comment $inputPath
    if ($checkMarker -eq $markerTagSuccess -or $checkMarker -eq $markerTagBloat) {
        $currentReason = if ($checkMarker -eq $markerTagSuccess) { "属于已压缩成功视频" } else { "属于历史压制膨胀视频（无压缩价值）" }
        
        if ($isSingleFileMode) {
            Write-Host "🔍 提示：检测到该文件元信息包含标识 [$checkMarker] ($currentReason)。" -ForegroundColor Cyan
            $choice = Read-Host "是否强行重新压缩该视频？[Y:继续压缩 / N:放弃退出] (默认 N)"
            if ($choice -ine "y") {
                Write-Host "已取消操作。" -ForegroundColor Gray
                $skipCount++
                continue
            }
            Write-Host "👉 已确认强行重压..." -ForegroundColor Orange
        } else {
            Write-Host "⏭️  检测到该文件符合拦截条件 [$checkMarker] ($currentReason)，批量模式下已自动跳过！" -ForegroundColor Cyan
            $skipCount++
            continue
        }
    }

    # 定义临时文件与最终文件路径
    $tempOutput = Join-Path $parentDir "${fileNameOnly}_temp_p7_compressed.mp4"
    $finalOutput = Join-Path $parentDir "${fileNameOnly}_compressed.mp4"
    
    # 组装参数：-loglevel error + -stats
    $ffmpegArgs = @(
        "-loglevel", "error",
        "-i", $inputPath,
        "-c:v", "hevc_nvenc",
        "-preset", "p7",
        "-cq", $qValue,
        "-pix_fmt", "p010le",
        "-x265-params", "copy-pic-extradata=1",
        "-c:a", "copy",
        "-map_metadata", "0",
        "-movflags", "use_metadata_tags",
        "-stats",
        $tempOutput
    )
    
    Write-Host "🚀 FFmpeg 正在硬解压制中..." -ForegroundColor Gray
    & ffmpeg @ffmpegArgs

    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ FFmpeg 压制该视频失败: $($file.Name)"
        if (Test-Path $tempOutput) { Remove-Item $tempOutput -Force }
        $failCount++
        continue
    }
    
    # 临时检查压制后的体积
    $compressedFileInfo = Get-Item $tempOutput
    $compressedSizeByte = $compressedFileInfo.Length
    $compressedSizeMB = [Math]::Round($compressedSizeByte / 1MB, 2)
    
    # ✨ 核心拦截与反向打标机制
    if ($compressedSizeByte -ge $originalSizeByte) {
        $diffMB = [Math]::Round(($compressedSizeByte - $originalSizeByte) / 1MB, 2)
        Write-Host "⚠️  拦截：压缩后体积反而变大（增大了 $diffMB MB），已触发熔断保护！" -ForegroundColor DarkYellow
        Write-Host "🔥 正在清理膨胀文件，并为原视频元数据注入[膨胀跳过标识]..." -ForegroundColor Gray
        
        # 释放临时压缩文件
        if (Test-Path $tempOutput) { Remove-Item $tempOutput -Force }
        
        # 关键操作：使用 ExifTool 直接在【原视频】中打上“膨胀标识”，并克隆修改/创建时间确保无痕迹
        & exiftool "-Comment=$markerTagBloat" "-FileModifyDate<FileModifyDate" "-FileCreateDate<FileCreateDate" -overwrite_original $inputPath > $null
        
        Write-Host "🔒 原视频已安全打标。下次遇到该文件将直接秒跳过，绝不重复压制！" -ForegroundColor Gray
        $bloatCount++
        continue
    }
    
    # 运行 ExifTool 恢复新文件元数据并打上【成功标识】
    & exiftool -tagsFromFile $inputPath "-all:all>all:all" "-FileModifyDate<FileModifyDate" "-FileCreateDate<FileCreateDate" "-Comment=$markerTagSuccess" $tempOutput > $null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ ExifTool 恢复元数据并打标失败: $($file.Name)"
        if (Test-Path $tempOutput) { Remove-Item $tempOutput -Force }
        if (Test-Path "${tempOutput}_original") { Remove-Item "${tempOutput}_original" -Force }
        $failCount++
        continue
    }
    if (Test-Path "${tempOutput}_original") { Remove-Item "${tempOutput}_original" -Force }
    
    # 计算体积缩减数据
    $savedMB = [Math]::Round(($originalSizeByte - $compressedSizeByte) / 1MB, 2)
    $savedPercent = [Math]::Round(($savedMB / $originalSizeMB) * 100, 2)
    
    # 5. 体积缩减成功，实施文件覆盖/重命名策略
    if ($overwriteChoice -eq "2") {
        $targetOverwrittenPath = Join-Path $parentDir "${fileNameOnly}.mp4"
        if ($inputPath -ieq $targetOverwrittenPath) {
            $trashPath = Join-Path $parentDir "${fileNameOnly}_old_to_delete.bak"
            Rename-Item -Path $inputPath -NewName (Split-Path $trashPath -Leaf) -Force
            Rename-Item -Path $tempOutput -NewName (Split-Path $targetOverwrittenPath -Leaf) -Force
            if (Test-Path $trashPath) { Remove-Item $trashPath -Force }
        } else {
            Rename-Item -Path $tempOutput -NewName (Split-Path $targetOverwrittenPath -Leaf) -Force
            if (Test-Path $inputPath) { Remove-Item $inputPath -Force }
        }
        Write-Host "📉 成功瘦身！原文件: $originalSizeMB MB | 压缩后: $compressedSizeMB MB (节省了 $savedPercent%)" -ForegroundColor Green
    } else {
        Rename-Item -Path $tempOutput -NewName (Split-Path $finalOutput -Leaf) -Force
        Write-Host "📉 成功瘦身！原文件: $originalSizeMB MB | 压缩后: $compressedSizeMB MB (节省了 $savedPercent%)" -ForegroundColor Green
    }
    
    $successCount++
}

# 6. 统计报告与末尾暂停
Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "🎉 任务全部结束！" -ForegroundColor Green
Write-Host "成功瘦身: $successCount 个 | 体积变大打标拦截: $bloatCount 个 | 自动跳过/放弃操作: $skipCount 个 | 失败: $failCount 个" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Gray
Read-Host "请检查上方日志，按 [回车键] 退出窗口"