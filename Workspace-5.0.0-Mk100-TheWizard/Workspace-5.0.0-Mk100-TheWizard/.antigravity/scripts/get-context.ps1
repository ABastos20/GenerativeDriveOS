param (
    [string]$StoryId,
    [string]$Topic
)

Write-Host "[*] Searching for context related to Story $StoryId / Topic '$Topic'..."

$root = "..\..\"
$matches = @()

# 1. Find Story Document
if ($StoryId) {
    $storyFiles = Get-ChildItem -Path "$root\docs\sprints" -Recurse -Filter "*$StoryId*"
    foreach ($file in $storyFiles) {
        $matches += [PSCustomObject]@{ Type = "Story Doc"; Path = $file.FullName }
    }
}

# 2. Find Related Source Code (by Topic)
if ($Topic) {
    $srcFiles = Get-ChildItem -Path "$root\src" -Recurse -Include "*.py" | Select-String -Pattern $Topic -List
    foreach ($match in $srcFiles) {
        $matches += [PSCustomObject]@{ Type = "Source Code"; Path = $match.Path }
    }
}

# 3. Find Related Tests
if ($Topic) {
    $testFiles = Get-ChildItem -Path "$root\tests" -Recurse -Include "test_*.py" | Select-String -Pattern $Topic -List
    foreach ($match in $testFiles) {
        $matches += [PSCustomObject]@{ Type = "Test"; Path = $match.Path }
    }
}

# Output Results
if ($matches.Count -gt 0) {
    Write-Host "`n[+] Found $($matches.Count) relevant files:"
    $matches | Format-Table -AutoSize
} else {
    Write-Host "`n[!] No specific context found. Try a broader topic."
}
